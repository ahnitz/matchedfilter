"""The native boundary must reject malformed buffers before any writes."""
import sys

import numpy as np
import pytest
from matchedfilter import _core


@pytest.fixture(params=['flat','hier'])
def native(request):
    n=128
    f=_core.MF(n,1,1) if request.param=='flat' else _core.HMF(n, 1, 1, [64])
    if request.param=='hier': f.set_thresholds([0.])
    data=np.ones(n,np.complex64)
    f.set_data(0,data); f.set_template(0,data)
    return f,data  # hierarchical native ingestion retains the caller's pointer


def buffers(size=128,blocks=1):
    return [np.full(size,-777,np.int64),np.full(size,-777,np.complex64),
            np.full(size,-777,np.float32),np.full(blocks,-777,np.int32)]


@pytest.mark.parametrize('entry',['run','series'])
@pytest.mark.parametrize('short',[0,1,2,3])
def test_small_outputs_leave_backing_allocation_untouched(native,entry,short):
    f,data=native
    backing=buffers()
    exposed=list(backing)
    exposed[short]=backing[short][:1] if short!=3 else backing[short][:0]
    with pytest.raises(ValueError,match='output'):
        if entry=='run': f.run(0,1,0,1,1,0.,0,128,*exposed)
        else: f.run_series(data,np.array([0],np.uintp),np.array([0],np.uintp),
                           np.array([128],np.uintp),0,1,1,0.,*exposed)
    for a in backing: assert (a==-777).all()


@pytest.mark.parametrize('case',['empty','mismatched','unaligned_bytes','different_bins','overflow','zero_bins','bad_template'])
def test_malformed_series_layout(native,case):
    f,data=native
    st=np.array([0,0],np.uintp); ws=np.array([0,0],np.uintp); we=np.array([128,128],np.uintp)
    bs=1; t0=0
    if case=='empty': st=ws=we=np.empty(0,np.uintp)
    elif case=='mismatched': we=we[:1]
    elif case=='unaligned_bytes': st=b'x'
    elif case=='different_bins': we[1]=127
    elif case=='overflow': st[1]=np.iinfo(np.uintp).max
    elif case=='zero_bins': bs=0
    elif case=='bad_template': t0=1
    out=buffers(256,2)
    with pytest.raises(ValueError): f.run_series(data,st,ws,we,t0,1,bs,0.,*out)
    for a in out: assert (a==-777).all()


def test_scratch_reuse_and_optional_magnitude(native):
    f,data=native
    for bs in (128,1,16,128):
        count=128//bs
        out=buffers(count)
        out[2]=np.empty(0,np.float32)
        f.run(0,1,0,1,bs,0.,0,128,*out)
        assert out[0][0]==0
        assert out[1][0]==pytest.approx(128+0j)


PEAK=np.dtype([('index',np.int64),('re',np.float32),('im',np.float32)])


def buffer_calls(f,data,flat):
    """(name, method, args) for each binding that takes buffers: a valid call, a call refused
    after every buffer is taken, and calls with an invalid optional peaks or phase argument."""
    n=data.size
    st,ws,we=np.array([0],np.uintp),np.array([0],np.uintp),np.array([n],np.uintp)
    out,pk,ph=buffers(),np.zeros(n,PEAK),np.zeros(1,np.uint32)
    yield 'set_data',f.set_data,(0,data)
    yield 'set_data short',f.set_data,(0,data[:-1])
    yield 'set_template',f.set_template,(0,data)
    yield 'set_template row',f.set_template,(1,data)
    yield 'set_data_batch',f.set_data_batch,(0,data)
    yield 'set_data_batch range',f.set_data_batch,(1,data)
    yield 'set_template_batch',f.set_template_batch,(0,data)
    yield 'set_template_batch partial',f.set_template_batch,(0,data[:-1])
    yield 'run',f.run,(0,1,0,1,1,0.,0,n,*out)
    yield 'run peaks',f.run,(0,1,0,1,1,0.,0,n,*out,pk)
    yield 'run refused',f.run,(0,1,0,1,0,0.,0,n,*out,pk)
    head=(data,st,ws,we,0,1)
    yield 'run_series',f.run_series,(*head,1,0.,*out,pk,ph)
    yield 'run_series refused',f.run_series,(*head,0,0.,*out,pk,ph)
    yield 'run_series bad phase',f.run_series,(*head,1,0.,*out,pk,ph[:0])
    yield 'run_series read-only peaks',f.run_series,(*head,1,0.,*out,bytes(16*n),ph)
    yield 'run_series phase not a buffer',f.run_series,(*head,1,0.,*out,pk,1)
    if not flat: return
    # run_series_dif needs two data rows; on this plan's one the engine fails after the checks.
    yield 'run_series_dif engine fails',f.run_series_dif,(*head,2,0.,*out,pk,0,ph)
    g=_core.MF(n,2,1)
    g.set_template(0,data)
    for d in (0,1):
        bs=1 if d else 2
        yield 'run_series_dif %d'%d,g.run_series_dif,(*head,bs,0.,*out,pk,d,ph)
        yield 'run_series_dif %d refused'%d,g.run_series_dif,(*head,0,0.,*out,pk,d,ph)
        yield 'run_series_dif %d bad phase'%d,g.run_series_dif,(*head,bs,0.,*out,pk,d,ph[:0])
        yield 'run_series_dif %d read-only peaks'%d,g.run_series_dif,(*head,bs,0.,*out,
                                                                     bytes(16*n),d,ph)
        yield 'run_series_dif %d phase not a buffer'%d,g.run_series_dif,(*head,bs,0.,*out,pk,d,1)


def test_every_call_releases_the_buffers_it_takes(native,request):
    """A buffer taken and not released keeps a reference to its array. Each call, whether
    it returns or raises, must leave every array argument's reference count where it was."""
    f,data=native
    flat=request.node.callspec.params['native']=='flat'
    outcomes=set()
    for name,method,args in buffer_calls(f,data,flat):
        arrays=[a for a in args if isinstance(a,(np.ndarray,bytes))]
        before=[sys.getrefcount(a) for a in arrays]
        try:
            method(*args); outcomes.add('returned')
        except (ValueError,IndexError,TypeError,BufferError,RuntimeError):
            outcomes.add('raised')
        assert [sys.getrefcount(a) for a in arrays]==before,name
    assert outcomes=={'returned','raised'}
