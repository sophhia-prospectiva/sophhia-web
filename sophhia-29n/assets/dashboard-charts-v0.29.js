(function(root){
'use strict';
const definitions=[
 {key:'scenarios',title:'1 · Trayectoria de escenarios de gobernabilidad',description:'Estado ordinal documentado: 1 referencia/estabilidad; 2 vigilancia; 3 refuerzo explícito. No mide probabilidades ni permite comparar fuerza electoral entre escenarios.',reading:'El marco de escenarios se conserva cuando la ficha lo declara y cita su origen. La validación de una entrada no aprueba otras fichas ni esta codificación editorial.'},
 {key:'blocks',title:'2 · Balance dinámico de bloques',description:'Recuento de temas tratados por grupo en cada ficha. Es actividad documental, no capacidad de gobernar, intención de voto ni balance electoral. Los grupos pueden solaparse.',reading:'El antiguo balance 0–100 no tiene una derivación verificable. Esta vista ofrece referencias documentales auditables; no lo sustituye por una estimación de escaños.'},
 {key:'variables',title:'3 · Pulso temporal de variables críticas',description:'Atención documental ordinal: 1 mención/contexto; 2 seguimiento explícito; 3 atención alta/intensificación. No son pesos MICMAC ni intensidad real de la variable.',reading:'Se aplica la misma regla a toda la serie. Una variable sin registro admisible queda sin codificar: su silencio no demuestra pérdida de relevancia.'},
 {key:'territorial',title:'4 · Pulso nacional‑territorial',description:'Misma escala de atención 1–3, con códigos territoriales canónicos. Sin cambios en la matriz MICMAC.',reading:'V10 · agenda vasca no tiene registro suficiente en estas fichas y queda sin datos. La actividad de Vox en Ceuta no se atribuye a V9 · agenda catalana.'},
 {key:'signals',title:'5 · Registro temporal de señales prospectivas',description:'Temas externos tratados por categoría en cada entrada; no cuenta acontecimientos nuevos acumulativos. Cada unidad tiene ID y una sola clase.',reading:'Se excluyen actuaciones internas, referencias genéricas y hechos no admisibles al corte. Cero significa ninguna unidad clasificada en la ficha, no ausencia de sucesos en el mundo.'}
];
const colors=['a','b','d','e','c','f'];
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel=d=>new Intl.DateTimeFormat('es-ES',{day:'numeric',month:'short',timeZone:'UTC'}).format(new Date(d+'T12:00:00Z'));
const numeric=x=>typeof x==='number'&&Number.isFinite(x);
function renderChart(data,key,width){
 const timeline=data.timeline,series=data[key], W=Math.max(240,Math.round(width||900)),H=W<420?270:300;
 const L=37,R=18,T=28,B=H-55,plotW=W-L-R,plotH=B-T;
 const t=timeline.map(d=>Date.parse(d.date+'T12:00:00Z'));const span=t[t.length-1]-t[0]||1;
 const X=i=>L+(t[i]-t[0])/span*plotW;
 const vals=Object.values(series).flat().filter(numeric);const ordinal=data.metric_types&&data.metric_types[key]==='ordinal_1_3';const top=ordinal?3:Math.max(4,Math.ceil(Math.max(0,...vals)/2)*2);
 const Y=v=>B-v/top*plotH;const ticks=ordinal?[1,2,3]:[0,top/2,top];
 const latest=timeline.reduce((last,_,i)=>Object.values(series).some(a=>numeric(a[i]))?i:last,-1);
 let s='<svg class="chart-svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" role="img" aria-labelledby="'+key+'-svg-title '+key+'-svg-desc"><title id="'+key+'-svg-title">'+esc(definitions.find(x=>x.key===key).title)+'</title><desc id="'+key+'-svg-desc">Eje temporal del '+timeline[0].date+' al '+timeline[timeline.length-1].date+'. Los días sin valor quedan vacíos; no se interpolan.</desc>';
 s+='<rect class="chart-plot-area" x="'+L+'" y="'+T+'" width="'+plotW+'" height="'+plotH+'" fill="var(--bg)"/>';
 const minorStep=ordinal?0.5:top/4;
 for(let v=minorStep;v<top;v+=minorStep){if(ticks.includes(v))continue;s+='<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'" stroke="var(--muted)" opacity=".18" stroke-width=".7"/>';}
 timeline.forEach((d,i)=>{s+='<line x1="'+X(i)+'" x2="'+X(i)+'" y1="'+T+'" y2="'+B+'" stroke="var(--muted)" opacity=".2" stroke-width=".7"/>';if(i<timeline.length-1){const x=(X(i)+X(i+1))/2;s+='<line x1="'+x+'" x2="'+x+'" y1="'+T+'" y2="'+B+'" stroke="var(--muted)" opacity=".1" stroke-width=".6"/>';}});
 if(latest<timeline.length-1){const start=latest<0?L:(X(latest)+X(latest+1))/2;s+='<rect class="chart-pending-area" x="'+start+'" y="'+T+'" width="'+(W-R-start)+'" height="'+plotH+'"/><text class="axis-label" x="'+((start+W-R)/2)+'" y="'+(T+16)+'" text-anchor="middle">'+(W<420?'Sin dato nuevo':'Sin nueva codificación')+'</text>';}
 timeline.forEach((d,i)=>{if(!Object.values(series).some(a=>numeric(a[i]))){const left=i===0?L:(X(i-1)+X(i))/2,right=i===timeline.length-1?W-R:(X(i)+X(i+1))/2;s+='<rect class="chart-missing-day" x="'+left+'" y="'+T+'" width="'+(right-left)+'" height="'+plotH+'"><title>'+esc(dateLabel(d.date)+': sin codificación admisible')+'</title></rect>';}});
 ticks.forEach(v=>{s+='<line class="gridline" x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'"/><text class="axis-label" x="'+(L-8)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+v+'</text>'});
 s+='<line class="axis" x1="'+L+'" x2="'+(W-R)+'" y1="'+B+'" y2="'+B+'"/>';
 const stride=W<420?3:W<650?2:1;
 timeline.forEach((d,i)=>{if(i!==timeline.length-1&&(i%stride||(i>0&&X(timeline.length-1)-X(i)<52)))return;s+='<text class="axis-label" x="'+X(i)+'" y="'+(B+20)+'" text-anchor="'+(i===0?'start':i===timeline.length-1?'end':'middle')+'">'+esc(dateLabel(d.date))+'</text>'});
 Object.entries(series).forEach(([name,a],j)=>{
  const color=colors[j%colors.length];let seg=[];const flush=()=>{if(seg.length>1)s+='<polyline class="line-series series-'+color+'" points="'+seg.join(' ')+'"/>';seg=[]};
  a.forEach((v,i)=>{if(!numeric(v)){flush();return}const x=X(i),y=Y(v),label=name+' · '+dateLabel(timeline[i].date)+' · '+v+' · codificación editorial pendiente IH';
   if(key==='signals'||key==='blocks'){const slot=plotW/Math.max(1,timeline.length-1),bw=Math.min(15,slot*.15),group=Object.keys(series).length*bw,center=Math.max(L+group/2,Math.min(W-R-group/2,x)),bx=center-group/2+j*bw;s+='<rect class="bar-'+color+'" x="'+bx+'" y="'+y+'" width="'+(bw*.85)+'" height="'+(B-y)+'"><title>'+esc(label)+'</title></rect>';}
   else{if(ordinal&&seg.length){const previous=seg[seg.length-1].split(',');seg.push(x+','+previous[1]);}seg.push(x+','+y);s+='<circle class="dotpt series-'+color+'" cx="'+x+'" cy="'+y+'" r="3.5"><title>'+esc(label)+'</title></circle>';}
  });flush();
 });
 s+='</svg>';return s;
}
function card(data,def,width){
 const latest=data.timeline.reduce((last,d,i)=>Object.values(data[def.key]).some(a=>numeric(a[i]))?i:last,-1);
 const last=latest<0?'Sin valores':dateLabel(data.timeline[latest].date)+' 2026';
 const entries=Object.entries(data[def.key]);
 return '<h4>'+esc(def.title)+'</h4><p>'+esc(def.description)+'</p><p class="chart-cut"><strong>Seguimiento hasta el '+esc(dateLabel(data.cutoff))+' 2026</strong> · Última codificación: '+esc(last)+'</p><div class="chart-wrap">'+renderChart(data,def.key,width)+'</div><div class="legend">'+entries.map(([name],i)=>'<span><i class="'+colors[i%colors.length]+'"></i>'+esc(name)+'</span>').join('')+'</div><p class="chart-note">Seguimiento documental · regla v1 · pendiente de validación IH. Los huecos no se interpolan; los escalones son estados ordinales, no trayectorias continuas.</p><p class="chart-reading">'+esc(data.readings&&data.readings[def.key]||def.reading)+'</p><details class="chart-values"><summary>Consultar valores, estado y evidencias</summary>'+data.timeline.map((d,i)=>'<p><strong>'+esc(d.entry+' · '+dateLabel(d.date))+'</strong> '+(d.source_status&&d.source_status.includes('borrador')?'[fuente: borrador pendiente IH] ':'')+'— '+esc(entries.map(([name,a])=>name+': '+(numeric(a[i])?a[i]:'sin registro específico')).join(' ; '))+(d.reconstructed_on?' · reconstruido el '+esc(dateLabel(d.reconstructed_on))+'; pendiente IH':'')+' · <a href="diario/'+d.date+'.html">Entrada del día</a></p>').join('')+'</details>';
}
function synchronize(data,index,current){
 const known=new Map(data.timeline.map((d,i)=>[d.date,i]));const all=[...index.entradas].filter(e=>e.fecha<=current.fecha).sort((a,b)=>a.fecha.localeCompare(b.fecha));
 const out={...data,cutoff:current.fecha,timeline:all.map(e=>({...((known.has(e.fecha)&&data.timeline[known.get(e.fecha)])||{}),date:e.fecha,entry:e.codigo,source_status:e.estado}))};
 definitions.forEach(def=>out[def.key]=Object.fromEntries(Object.entries(data[def.key]).map(([k,a])=>[k,all.map(e=>known.has(e.fecha)?a[known.get(e.fecha)]??null:null)])));
 return out;
}
function coverageSummary(data){
 const coverage=definitions.map(def=>{const last=data.timeline.reduce((v,d,i)=>Object.values(data[def.key]).some(a=>numeric(a[i]))?d.date:v,null);return {key:def.key,last};});
 const complete=coverage.every(c=>c.last===data.cutoff);
 return (complete?'Datos gráficos hasta el '+dateLabel(data.cutoff)+' 2026. ':'Cobertura gráfica: '+coverage.map(c=>c.key+' '+(c.last?dateLabel(c.last):'sin valores')).join('; ')+'. ')+(data.reconstructions&&data.reconstructions.some(r=>r.from==='2026-10-18')?'Reconstrucción 18–24 realizada el 24 oct. ':'')+'Regla v1; codificación pendiente IH. Los huecos no se rellenan.';
}
const api={definitions,renderChart,card,synchronize,coverageSummary};if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(typeof document==='undefined')return;
function init(){const container=document.getElementById('dashboard-temporal-charts');if(!container)return;let data=JSON.parse(document.getElementById('dashboard-chart-data').textContent);let lastWidth=0;
 function draw(){const W=Math.round(container.clientWidth)-34;if(Math.abs(W-lastWidth)<2&&lastWidth)return;lastWidth=W;container.innerHTML=definitions.map(def=>'<article class="chart-card wide" data-chart="'+def.key+'">'+card(data,def,W)+'</article>').join('')}
 draw();if(typeof ResizeObserver!=='undefined')new ResizeObserver(draw).observe(container);else window.addEventListener('resize',draw);
 Promise.all(['data/dashboard_timeseries.json','data/diario_index.json','data/current.json'].map(url=>fetch(url,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Datos inaccesibles');return r.json()}))).then(([fresh,index,current])=>{data=synchronize(fresh,index,current);lastWidth=0;draw();document.getElementById('dashboard-chart-sync').textContent=coverageSummary(data)}).catch(()=>{document.getElementById('dashboard-chart-sync').textContent='Versión editorial conservada · '+dateLabel(data.cutoff)+' 2026. Sincronización en directo no confirmada.'})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})(typeof globalThis!=='undefined'?globalThis:this);

