"""Embed recorded teaser comparisons in the hardware comparison page."""
import html
import json
from pathlib import Path
from teaser_labels import hardware_label


def fleet_comparison(root):
    m_dir = Path(root)/'docs/measurements'
    teaser_files = sorted(m_dir.glob('teaser-fleet-*.json')) if m_dir.is_dir() else []
    if not teaser_files:
        path = Path(root)/'docs/measurements/teaser-fleet-20260928.json'
        if not path.is_file():
            return ''
        teaser_files = [path]
    teaser_path = teaser_files[-1]
    reports = json.loads(teaser_path.read_text())['reports']
    compact = [{k: r[k] for k in ('host', 'cpu', 'gpu', 'device', 'rows', 'errors')}
               for r in reports]
    for record, source in zip(compact, reports):
        record['label'] = hardware_label(source)
    data = json.dumps(compact).replace('<', '\\u003c')

    gpu512_files = sorted(m_dir.glob('gpu-fleet-512x512-*.json')) if m_dir.is_dir() else []
    gpu512_path = gpu512_files[-1] if gpu512_files else None
    gpu512_compact = []
    gpu512_data = '[]'
    if gpu512_path and gpu512_path.is_file():
        gpu512_reports = json.loads(gpu512_path.read_text())['reports']
        gpu512_compact = [{k: r.get(k) for k in ('host', 'cpu', 'gpu', 'device', 'rows', 'errors')}
                          for r in gpu512_reports]
        for record, source in zip(gpu512_compact, gpu512_reports):
            record['label'] = hardware_label(source)
        gpu512_data = json.dumps(gpu512_compact).replace('<', '\\u003c')

    btn_actions = ('<span class="fleet-actions">'
                   '<button type="button" class="fleet-btn" data-action="all">Select all</button>'
                   '<button type="button" class="fleet-btn" data-action="none">Unselect all</button>'
                   '</span>')
    def hardware_inputs(reps, dev_type, input_name='fleet-hardware'):
        return ''.join('<label><input type="checkbox" name="%s" value="%s" checked> %s</label>'
                       % (input_name, html.escape(r['host']+':'+r['device'], quote=True), html.escape(r['label']))
                       for r in reps if r['device'] == dev_type and (r['rows'] or any('check failed' in e for e in r['errors'])))

    cpu_inputs = hardware_inputs(compact, 'cpu')
    gpu_inputs = hardware_inputs(compact, 'gpu')
    other_inputs = ''.join('<label><input type="checkbox" name="fleet-hardware" value="%s" checked> %s</label>'
                          % (html.escape(r['host']+':'+r['device'], quote=True), html.escape(r['label']))
                          for r in compact if r['device'] not in ('cpu', 'gpu') and (r['rows'] or any('check failed' in e for e in r['errors'])))

    hardware_boxes = []
    if cpu_inputs:
        hardware_boxes.append('<fieldset><legend>CPUs ' + btn_actions + '</legend>' + cpu_inputs + '</fieldset>')
    if gpu_inputs:
        hardware_boxes.append('<fieldset><legend>GPUs ' + btn_actions + '</legend>' + gpu_inputs + '</fieldset>')
    if other_inputs:
        hardware_boxes.append('<fieldset><legend>Other devices ' + btn_actions + '</legend>' + other_inputs + '</fieldset>')
    hardware_fieldsets = ''.join(hardware_boxes)

    gpu512_fieldsets = ''
    if gpu512_compact:
        gpu512_gpu_inputs = hardware_inputs(gpu512_compact, 'gpu', input_name='fleet-hardware-512')
        if gpu512_gpu_inputs:
            gpu512_fieldsets = '<fieldset><legend>GPUs ' + btn_actions + '</legend>' + gpu512_gpu_inputs + '</fieldset>'

    outputs = [('baseline', 'FFT only'), ('full', 'Full output'), ('flat', 'Peak only')]
    budgets = [('hier:0.01', 'FDR 10⁻²'), ('hier:0.001', 'FDR 10⁻³'),
               ('hier:0.0001', 'FDR 10⁻⁴')]
    choices = ''.join('<label><input type="checkbox" name="fleet-mode" value="%s" checked> %s</label>'
                      % pair for pair in outputs)
    budget_choices = ''.join(
        '<label><input type="checkbox" name="fleet-mode" value="%s"%s> %s</label>'
        % (k, ' checked' if k == 'hier:0.001' else '', t) for k, t in budgets)

    snrs = sorted({r['snr'] for rep in compact for r in rep['rows']
                   if r.get('kind') == 'hier' and r.get('snr') is not None})
    if gpu512_compact:
        snrs = sorted(set(snrs).union({r['snr'] for rep in gpu512_compact for r in rep['rows']
                                       if r.get('kind') == 'hier' and r.get('snr') is not None}))
    default_snr = 5.5 if 5.5 in snrs else (snrs[0] if snrs else None)
    snr_choices = ''.join(
        '<label><input type="checkbox" name="fleet-snr" value="%s"%s> %g</label>'
        % (('%g' % v), ' checked' if v == default_snr else '', v) for v in snrs)
    hier_fieldset = ('<fieldset><legend>Hierarchical screening</legend>'
                     + budget_choices
                     + ('<span class="fleet-sep">SNR threshold</span>' + snr_choices
                        if snrs else '')
                     + '</fieldset>')

    workload_fieldset = ''
    if gpu512_compact:
        workload_fieldset = (
            '<fieldset id="fleet-workload-fieldset"><legend>Workload</legend>'
            '<label><input type="radio" name="fleet-workload" value="teaser" checked> 16 &times; 512 (8,192 correlations &middot; CPU &amp; GPU fleet)</label>'
            '<label><input type="radio" name="fleet-workload" value="prod512"> 512 &times; 512 (262,144 correlations &middot; GPU production fleet: A100, L40S, A40, 8060S, M2)</label>'
            '</fieldset>'
        )

    date_str = 'October 3, 2026' if '20261003' in teaser_path.name else 'September 28, 2026'
    download_links = f'<a href="assets/{teaser_path.name}" download>{teaser_path.name}</a>'
    if gpu512_path:
        download_links += f' and <a href="assets/{gpu512_path.name}" download>{gpu512_path.name}</a>'

    hw_containers = (
        '<div id="fleet-hw-teaser">' + hardware_fieldsets + '</div>'
        + ('<div id="fleet-hw-prod512" style="display:none">' + gpu512_fieldsets + '</div>' if gpu512_compact else '')
    )

    return '''<section id="machine-comparison" aria-labelledby="fleet-title">
<h2 id="fleet-title">Compare hardware and output modes</h2>
<p id="fleet-desc">8,192 correlations × 4,096 points: 16 data spectra and 512 templates.
Warm public <code>run()</code> calls, one CPU thread, setup and upload excluded;
GPU synchronization included. Hierarchical rows use the captured PyCBC reference
profile and are recorded at several SNR thresholds. Recorded ''' + date_str + '''.</p>
<div class="fleet-controls">''' + workload_fieldset + hw_containers + '''
<fieldset><legend>Outputs</legend>''' + choices + '''</fieldset>''' + hier_fieldset + '''
<fieldset><legend>Display</legend>
<label>Axis <select id="fleet-scale"><option value="linear">Linear (equal spacing)</option><option value="log" selected>Logarithmic</option></select></label>
<label>Measure <select id="fleet-metric"><option value="rate">Throughput (higher is better)</option><option value="time">Milliseconds (lower is better)</option></select></label>
<label><input type="checkbox" id="fleet-shared" checked> Same axis range for CPU and GPU</label>
</fieldset></div>
<p id="fleet-status" role="status" aria-live="polite"></p>
<div id="fleet-charts"></div>
<div id="fleet-fallback"><img src="assets/teaser-fleet.svg" alt="Recorded CPU and GPU comparison across machines"><p>Enable JavaScript to change the comparison.</p></div>
<p class="fleet-caption">Full output → peaks avoids writing every lag; hierarchy also skips most full transforms.
Automatic coarse choices vary by device; requested dismissal budgets are not measured here.
Whiskers show timing-block 10th–90th percentiles, not confidence intervals.</p>
<p>FFT-only references: FFTW on CPU, cuFFT on NVIDIA, rocFFT on Radeon 8060S, MLX on M2.
Missing references and failed checks are shown explicitly; software GPUs are excluded.
The Xeon result is from a virtual machine. All timing samples and configuration details are in the
recorded JSON (''' + download_links + ''').</p>
<details><summary>Selected timings and availability</summary><div id="fleet-table"></div></details>
<style>
#machine-comparison .fleet-controls{display:grid;gap:.6rem}
#machine-comparison fieldset{border:1px solid var(--rule);border-radius:6px;padding:.6rem;display:flex;flex-wrap:wrap;gap:.4rem 1rem}
#machine-comparison legend{font-weight:600;font-size:.9rem;padding:0 .3rem}
#machine-comparison .fleet-actions{display:inline-flex;gap:.3rem;margin-left:.6rem;font-weight:normal;vertical-align:middle}
#machine-comparison .fleet-btn{background:var(--panel);color:var(--fg);border:1px solid var(--rule);border-radius:4px;padding:.1rem .45rem;font:11px/1.4 system-ui,sans-serif;cursor:pointer}
#machine-comparison .fleet-btn:hover{border-color:var(--accent);color:var(--accent)}
#machine-comparison .fleet-btn:active{transform:translateY(1px)}
#machine-comparison label{display:inline-flex;align-items:center;gap:.3rem;font:13px/1.5 system-ui,sans-serif}
#machine-comparison select{background:var(--bg);color:var(--fg);border:1px solid var(--rule);border-radius:4px;padding:.3rem}
#fleet-charts{display:grid;gap:1rem}#fleet-charts figure{margin:0;overflow-x:auto}
#fleet-charts svg{width:100%;min-width:650px;height:auto;display:block}
#fleet-charts text{font-family:system-ui,sans-serif;fill:var(--fg)}
#fleet-table{overflow-x:auto}#fleet-fallback img{width:100%}
#machine-comparison .fleet-caption{font-size:.85rem;color:var(--mut)}
#machine-comparison .fleet-sep{display:inline-block;margin:0 .4rem 0 .9rem;font-size:.85rem;color:var(--mut);border-left:1px solid var(--rule);padding-left:.9rem}
</style>
<script type="application/json" id="fleet-records">''' + data + '''</script>
''' + ('<script type="application/json" id="fleet-records-512">' + gpu512_data + '</script>' if gpu512_compact else '') + '''
<script>
(()=>{
 const root=document.getElementById('machine-comparison');
 const reportsTeaser=JSON.parse(document.getElementById('fleet-records').textContent);
 const el512=document.getElementById('fleet-records-512');
 const reports512=el512?JSON.parse(el512.textContent):[];
 const MEASURED_SNRS=''' + json.dumps(snrs) + ''';
 const modes=[['baseline','FFT only','#94a3b8'],['full','Full output','#ad9aff'],['flat','Peak only','#38bdf8'],['hier:0.01','Hier. 10⁻²','#34d399'],['hier:0.001','Hier. 10⁻³','#25b995'],['hier:0.0001','Hier. 10⁻⁴','#efbb64']];
 const shade=(hex,i,n)=>{if(n<2)return hex;const t=-0.34+0.68*(i/(n-1));
  const v=parseInt(hex.slice(1),16),to=t<0?0:255,k=Math.abs(t);
  const mix=c=>Math.round(c+(to-c)*k).toString(16).padStart(2,'0');
  return '#'+mix((v>>16)&255)+mix((v>>8)&255)+mix(v&255);};
 function seriesFor(wanted){
  const snrs=[...selected('fleet-snr')].map(Number).sort((a,b)=>a-b);
  const out=[];
  for(const m of modes){
   if(!wanted.has(m[0]))continue;
   if(m[0].slice(0,5)!=='hier:'){out.push({label:m[1],color:m[2],match:r=>r.kind===m[0]});continue;}
   const fd=Number(m[0].slice(5));
   if(!MEASURED_SNRS.length){out.push({label:m[1],color:m[2],match:r=>r.kind==='hier'&&Number(r.fd)===fd});continue;}
   if(!snrs.length)continue;
   snrs.forEach((v,i)=>out.push({label:m[1]+' · SNR '+v,color:shade(m[2],i,snrs.length),
    match:r=>r.kind==='hier'&&Number(r.fd)===fd&&(r.snr==null||Number(r.snr)===v)}));
  }
  return out;}
 const selected=name=>new Set([...root.querySelectorAll('input[name="'+name+'"]:checked')].map(e=>e.value));
 const el=(tag,text)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;return e;};
 const svgEl=(tag,attrs,text)=>{const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))e.setAttribute(k,v);if(text!==undefined)e.textContent=text;return e;};
 const pct=(a,q)=>{const s=[...a].sort((a,b)=>a-b),i=(s.length-1)*q,l=Math.floor(i);return s[l]+(s[Math.ceil(i)]-s[l])*(i-l);};
 function onWorkloadChange(){
  const wl=root.querySelector('input[name="fleet-workload"]:checked')?.value||'teaser';
  const hwTeaser=root.querySelector('#fleet-hw-teaser');
  const hw512=root.querySelector('#fleet-hw-prod512');
  const desc=root.querySelector('#fleet-desc');
  if(wl==='prod512'&&hw512){
   if(hwTeaser)hwTeaser.style.display='none';
   hw512.style.display='block';
   if(desc)desc.innerHTML='262,144 correlations × 4,096 points: 512 data spectra and 512 templates. Warm public <code>run()</code> calls, enterprise-scale GPU production workload with full plan burn-in and steady-state GPU clocks; setup and upload excluded; GPU synchronization included. Hierarchical rows use the captured PyCBC reference profile. Recorded October 3, 2026.';
  } else {
   if(hw512)hw512.style.display='none';
   if(hwTeaser)hwTeaser.style.display='block';
   if(desc)desc.innerHTML='8,192 correlations × 4,096 points: 16 data spectra and 512 templates. Warm public <code>run()</code> calls, one CPU thread, setup and upload excluded; GPU synchronization included. Hierarchical rows use the captured PyCBC reference profile and are recorded at several SNR thresholds. Recorded ''' + date_str + '''.';
  }
 }
 function render(){
  const wl=root.querySelector('input[name="fleet-workload"]:checked')?.value||'teaser';
  const is512=wl==='prod512'&&reports512.length>0;
  const reports=is512?reports512:reportsTeaser;
  const pairs=is512?262144:8192;
  const hwName=is512?'fleet-hardware-512':'fleet-hardware';
  const hardware=selected(hwName), wanted=selected('fleet-mode');
  const series=seriesFor(wanted), shown=r=>series.some(q=>q.match(r));
  const logarithmic=root.querySelector('#fleet-scale').value==='log', time=root.querySelector('#fleet-metric').value==='time';
  const shared=root.querySelector('#fleet-shared').checked;
  const chosen=reports.filter(r=>hardware.has(r.host+':'+r.device));
  const value=r=>time?r.ms:pairs/r.ms/1000;
  const allRows=chosen.flatMap(r=>r.rows.filter(shown));
  const charts=root.querySelector('#fleet-charts');charts.replaceChildren();
  const table=el('table'),head=el('thead'),hr=el('tr');
  ['Hardware','Device','Output','ms / batch','Million pairs / s'].forEach(t=>hr.append(el('th',t)));head.append(hr);table.append(head);const body=el('tbody');table.append(body);
  root.querySelector('#fleet-status').textContent=allRows.length?`${allRows.length} measured results across ${series.length} selected series (${pairs.toLocaleString()} pairs). ${time?'Lower latency':'Higher throughput'} is better. ${logarithmic?'Logarithmic':'Linear'} axis; ${shared?'shared':'independent'} CPU/GPU ranges.`:'Select hardware, outputs and — for hierarchical rows — at least one SNR threshold.';
  for(const device of ['cpu','gpu']){
   const groups=chosen.filter(r=>r.device===device),rows=groups.flatMap(r=>r.rows.filter(shown));
   if(!groups.length||!series.length)continue;
   const axisRows=shared?allRows:rows;
   const vals=axisRows.map(value), maximum=Math.max(...vals,1e-6);
   const low=logarithmic?10**Math.floor(Math.log10(Math.min(...vals,maximum)/1.2)):0;
   const high=logarithmic?10**Math.ceil(Math.log10(maximum*1.3)):maximum*1.3;
   const x=v=>215+565*(logarithmic?(Math.log10(v)-Math.log10(low))/(Math.log10(high)-Math.log10(low)):(v-low)/(high-low));
   const lines=groups.reduce((s,r)=>{const n=r.rows.filter(shown).length;return s+Math.max(1,n)*25+55+(n&&n<series.length?15:0);},0);
   const svg=svgEl('svg',{viewBox:`0 0 920 ${lines+90}`,role:'img','aria-label':device.toUpperCase()+' benchmark comparison'});
   svg.append(svgEl('title',{},device.toUpperCase()+' recorded performance'));
   const ticks=logarithmic?Array.from({length:Math.round(Math.log10(high/low))+1},(_,i)=>low*10**i):Array.from({length:6},(_,i)=>high*i/5);
   for(const t of ticks){svg.append(svgEl('line',{x1:x(t),x2:x(t),y1:35,y2:lines+35,stroke:'var(--rule)'}));svg.append(svgEl('text',{x:x(t),y:lines+57,'text-anchor':'middle','font-size':11},Number(t.toPrecision(3))+(time?' ms':'M/s')));}
   let y=35;svg.append(svgEl('text',{x:10,y:20,'font-size':17,'font-weight':600},device.toUpperCase()));
   for(const r of groups){
    svg.append(svgEl('text',{x:10,y:y+16,'font-size':13,'font-weight':600},r.label));
    y+=35;
    const found=series.map(q=>[q,r.rows.find(row=>q.match(row))]);
    const measured=found.filter(([,row])=>row);
    if(!measured.length){const reason=r.errors.some(e=>e.includes('check failed'))?'Validation failed':r.rows.length?'Selected output unavailable':'No physical GPU exposed';svg.append(svgEl('text',{x:215,y:y+12,'font-size':12},reason));const tr=el('tr');[r.label,device,reason,'—','—'].forEach(t=>tr.append(el('td',t)));body.append(tr);y+=25;}
    for(const [m,row] of measured){
     const v=value(row);svg.append(svgEl('text',{x:205,y:y+12,'text-anchor':'end','font-size':12},m.label));
     const rect=svgEl('rect',{x:215,y,width:Math.max(0,x(v)-215),height:17,fill:m.color});
     rect.append(svgEl('title',{},`${r.label}: ${row.ms.toFixed(4)} ms; ${(pairs/row.ms/1000).toFixed(3)}M pairs/s${row.cascade_band?'; cascade '+row.cascade_band+'/'+row.band+', refinement '+(100*row.refine_rate).toFixed(2)+'%':(row.band?'; band '+row.band+', refinement '+(100*row.refine_rate).toFixed(2)+'%':'')}`));svg.append(rect);
     const a=row.timing?.block_ms||[];let label=x(v);
     if(a.length){const lo=pct(a,.1),hi=pct(a,.9),left=time?lo:pairs/hi/1000,right=time?hi:pairs/lo/1000;svg.append(svgEl('line',{x1:x(left),x2:x(right),y1:y+8,y2:y+8,stroke:'var(--fg)','stroke-width':1.5}));label=Math.max(label,x(right));}
     svg.append(svgEl('text',{x:label+5,y:y+12,'font-size':11},time?row.ms.toFixed(3)+' ms':v.toFixed(3)+'M/s'));
     const tr=el('tr');[r.label,device,m.label,row.ms.toFixed(4),(pairs/row.ms/1000).toFixed(4)].forEach(t=>tr.append(el('td',t)));body.append(tr);y+=25;
    }
    if(found.some(([,row])=>!row)&&measured.length){svg.append(svgEl('text',{x:215,y:y+11,'font-size':10},'Some selected outputs have no measurement.'));y+=15;}
    y+=20;
   }
   const figure=el('figure');figure.append(svg);charts.append(figure);
  }
  root.querySelector('#fleet-table').replaceChildren(table);
 }
 root.querySelector('.fleet-controls').addEventListener('change',e=>{
  if(e.target.name==='fleet-workload')onWorkloadChange();
  render();
 });
 root.addEventListener('click',e=>{
  const btn=e.target.closest('.fleet-actions button');
  if(!btn)return;
  e.preventDefault();
  const fieldset=btn.closest('fieldset');
  const check=btn.dataset.action==='all';
  fieldset.querySelectorAll('input[type="checkbox"]').forEach(c=>{c.checked=check;});
  render();
 });
 render();root.querySelector('#fleet-fallback').hidden=true;
})();
</script></section>'''
