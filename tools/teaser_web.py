"""Embed recorded teaser comparisons in the hardware comparison page."""
import html
import json
from pathlib import Path
from teaser_labels import hardware_label


def fleet_comparison(root):
    path = Path(root)/'docs/measurements/teaser-fleet-20260928.json'
    if not path.is_file():
        return ''
    reports = json.loads(path.read_text())['reports']
    # Embed the records: the page works offline without a fetch or CDN.
    compact = [{k: r[k] for k in ('host', 'cpu', 'gpu', 'device', 'rows', 'errors')}
               for r in reports]
    for record, source in zip(compact, reports):
        record['label'] = hardware_label(source)
    data = json.dumps(compact).replace('<', '\\u003c')
    machines = ''.join('<label><input type="checkbox" name="fleet-hardware" value="%s" checked> %s</label>'
                       % (html.escape(r['host']+':'+r['device'], quote=True), html.escape(r['label']))
                       for r in compact if r['rows'] or any('check failed' in e for e in r['errors']))
    outputs = [('baseline', 'FFT only'), ('full', 'Full output'), ('flat', 'Peak only')]
    budgets = [('hier:0.01', 'FDR 10⁻²'), ('hier:0.001', 'FDR 10⁻³'),
               ('hier:0.0001', 'FDR 10⁻⁴')]
    choices = ''.join('<label><input type="checkbox" name="fleet-mode" value="%s" checked> %s</label>'
                      % pair for pair in outputs)
    # The budget and the detection threshold both belong to the hierarchy, and
    # both are multi-select: a reader comparing budgets at one threshold and a
    # reader comparing thresholds at one budget want the same control.
    budget_choices = ''.join(
        '<label><input type="checkbox" name="fleet-mode" value="%s"%s> %s</label>'
        % (k, ' checked' if k == 'hier:0.001' else '', t) for k, t in budgets)
    # SNR values actually present in the hierarchical rows, so the control
    # never offers a threshold that was not measured.
    snrs = sorted({r['snr'] for rep in compact for r in rep['rows']
                   if r.get('kind') == 'hier' and r.get('snr') is not None})
    default_snr = 5.5 if 5.5 in snrs else (snrs[0] if snrs else None)
    snr_choices = ''.join(
        '<label><input type="checkbox" name="fleet-snr" value="%s"%s> %g</label>'
        % (('%g' % v), ' checked' if v == default_snr else '', v) for v in snrs)
    hier_fieldset = ('<fieldset><legend>Hierarchical screening</legend>'
                     + budget_choices
                     + ('<span class="fleet-sep">SNR threshold</span>' + snr_choices
                        if snrs else '')
                     + '</fieldset>')
    return '''<section id="machine-comparison" aria-labelledby="fleet-title">
<h2 id="fleet-title">Compare hardware and output modes</h2>
<p>8,192 correlations × 4,096 points: 16 data spectra and 512 templates.
Warm public <code>run()</code> calls, one CPU thread, setup and upload excluded;
GPU synchronization included. Recorded September 26, 2026.</p>
<div class="fleet-controls">
<fieldset><legend>CPUs and GPUs</legend>''' + machines + '''</fieldset>
<fieldset><legend>Outputs</legend>''' + choices + '''</fieldset>''' + hier_fieldset + '''
<fieldset><legend>Display</legend>
<label>Axis <select id="fleet-scale"><option value="linear">Linear (equal spacing)</option><option value="log" selected>Logarithmic</option></select></label>
<label>Measure <select id="fleet-metric"><option value="rate">Throughput (higher is better)</option><option value="time">Milliseconds (lower is better)</option></select></label>
<label><input type="checkbox" id="fleet-shared" checked> Same axis range for CPU and GPU</label>
</fieldset></div>
<p id="fleet-status" role="status" aria-live="polite"></p>
<div id="fleet-charts"></div>
<div id="fleet-fallback"><img src="assets/teaser-fleet.svg" alt="Recorded CPU and GPU comparison across six machines"><p>Enable JavaScript to change the comparison.</p></div>
<p class="fleet-caption">Full output → peaks avoids writing every lag; hierarchy also skips most full transforms.
Automatic coarse choices vary by device; requested dismissal budgets are not measured here.
Whiskers show timing-block 10th–90th percentiles, not confidence intervals.</p>
<p>FFT-only references: FFTW on CPU, rocFFT on Radeon 8060S, MLX on M2.
Missing references and failed checks are shown explicitly; software GPUs are excluded.
The Xeon result is from a virtual machine. All timing samples and configuration details are in the
<a href="assets/teaser-fleet-20260928.json" download>recorded JSON</a>.</p>
<details><summary>Selected timings and availability</summary><div id="fleet-table"></div></details>
<style>
#machine-comparison .fleet-controls{display:grid;gap:.6rem}
#machine-comparison fieldset{border:1px solid var(--rule);border-radius:6px;padding:.6rem;display:flex;flex-wrap:wrap;gap:.4rem 1rem}
#machine-comparison legend{font-weight:600;font-size:.9rem;padding:0 .3rem}
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
<script>
(()=>{
 const root=document.getElementById('machine-comparison');
 const reports=JSON.parse(document.getElementById('fleet-records').textContent);
 const MEASURED_SNRS=''' + json.dumps(snrs) + ''';
 const modes=[['baseline','FFT only','#94a3b8'],['full','Full output','#ad9aff'],['flat','Peak only','#38bdf8'],['hier:0.01','Hier. 10⁻²','#34d399'],['hier:0.001','Hier. 10⁻³','#25b995'],['hier:0.0001','Hier. 10⁻⁴','#efbb64']];
 // Shade one budget's colour across the selected thresholds, so a budget
 // stays recognisable while each threshold is still distinguishable.
 const shade=(hex,i,n)=>{if(n<2)return hex;const t=-0.34+0.68*(i/(n-1));
  const v=parseInt(hex.slice(1),16),to=t<0?0:255,k=Math.abs(t);
  const mix=c=>Math.round(c+(to-c)*k).toString(16).padStart(2,'0');
  return '#'+mix((v>>16)&255)+mix((v>>8)&255)+mix(v&255);};
 // A hierarchical series is one (budget, threshold) pair: both controls are
 // multi-select, so a budget alone no longer identifies a row.
 function seriesFor(wanted){
  const snrs=[...selected('fleet-snr')].map(Number).sort((a,b)=>a-b);
  const out=[];
  for(const m of modes){
   if(!wanted.has(m[0]))continue;
   if(m[0].slice(0,5)!=='hier:'){out.push({label:m[1],color:m[2],match:r=>r.kind===m[0]});continue;}
   const fd=Number(m[0].slice(5));
   // No thresholds RECORDED (older data) means the budget is the whole
   // series. Thresholds recorded but none ticked means the reader asked for
   // no hierarchical rows -- not for all of them overlaid.
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
 function render(){
  const hardware=selected('fleet-hardware'), wanted=selected('fleet-mode');
  const series=seriesFor(wanted), shown=r=>series.some(q=>q.match(r));
  const logarithmic=root.querySelector('#fleet-scale').value==='log', time=root.querySelector('#fleet-metric').value==='time';
  const shared=root.querySelector('#fleet-shared').checked;
  const chosen=reports.filter(r=>hardware.has(r.host+':'+r.device));
  const value=r=>time?r.ms:8192/r.ms/1000;
  const allRows=chosen.flatMap(r=>r.rows.filter(shown));
  const charts=root.querySelector('#fleet-charts');charts.replaceChildren();
  const table=el('table'),head=el('thead'),hr=el('tr');
  ['Hardware','Device','Output','ms / batch','Million pairs / s'].forEach(t=>hr.append(el('th',t)));head.append(hr);table.append(head);const body=el('tbody');table.append(body);
  root.querySelector('#fleet-status').textContent=allRows.length?`${allRows.length} measured results across ${series.length} selected series. ${time?'Lower latency':'Higher throughput'} is better. ${logarithmic?'Logarithmic':'Linear'} axis; ${shared?'shared':'independent'} CPU/GPU ranges.`:'Select hardware, outputs and — for hierarchical rows — at least one SNR threshold.';
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
     rect.append(svgEl('title',{},`${r.label}: ${row.ms.toFixed(4)} ms; ${(8192/row.ms/1000).toFixed(3)}M pairs/s${row.band?'; band '+row.band+', refinement '+(100*row.refine_rate).toFixed(2)+'%':''}`));svg.append(rect);
     const a=row.timing?.block_ms||[];let label=x(v);
     if(a.length){const lo=pct(a,.1),hi=pct(a,.9),left=time?lo:8192/hi/1000,right=time?hi:8192/lo/1000;svg.append(svgEl('line',{x1:x(left),x2:x(right),y1:y+8,y2:y+8,stroke:'var(--fg)','stroke-width':1.5}));label=Math.max(label,x(right));}
     svg.append(svgEl('text',{x:label+5,y:y+12,'font-size':11},time?row.ms.toFixed(3)+' ms':v.toFixed(3)+'M/s'));
     const tr=el('tr');[r.label,device,m.label,row.ms.toFixed(4),(8192/row.ms/1000).toFixed(4)].forEach(t=>tr.append(el('td',t)));body.append(tr);y+=25;
    }
    if(found.some(([,row])=>!row)&&measured.length){svg.append(svgEl('text',{x:215,y:y+11,'font-size':10},'Some selected outputs have no measurement.'));y+=15;}
    y+=20;
   }
   const figure=el('figure');figure.append(svg);charts.append(figure);
  }
  root.querySelector('#fleet-table').replaceChildren(table);
 }
 root.querySelector('.fleet-controls').addEventListener('change',render);
 render();root.querySelector('#fleet-fallback').hidden=true;
})();
</script></section>'''
