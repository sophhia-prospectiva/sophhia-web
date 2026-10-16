(function(root){
'use strict';
const definitions=[
 {key:'scenarios',title:'1 · Trayectoria de escenarios de gobernabilidad',description:'Indicadores históricos de plausibilidad relativa. No son probabilidades ni porcentajes de voto.',reading:'D-010 · 16 oct: marco A-000 conservado, sin recalibración. No se han calculado nuevas puntuaciones.'},
 {key:'blocks',title:'2 · Balance dinámico de bloques',description:'Indicadores históricos de capacidad relativa de gobernabilidad. No son escaños ni intención de voto.',reading:'D-010 · 16 oct: alianzas territoriales en seguimiento. No hay un nuevo cálculo de balance de bloques.'},
 {key:'variables',title:'3 · Pulso temporal de variables críticas',description:'Indicadores históricos de centralidad de las variables. Escala heurística, sin medición estadística.',reading:'D-010 · 16 oct: recomposición de candidaturas, vivienda y garantías siguen bajo vigilancia. Sin puntuaciones nuevas.'},
 {key:'territorial',title:'4 · Pulso nacional‑territorial',description:'Indicadores históricos de vigilancia territorial. No equivalen a pesos de la matriz MICMAC.',reading:'D-010 · 16 oct: acuerdos territoriales y compatibilidad de pactos en vigilancia. MICMAC v0.2 sin modificar.'},
 {key:'signals',title:'5 · Registro temporal de señales prospectivas',description:'Recuento histórico por categoría. Un dato pendiente no significa que ese día no haya señales.',reading:'D-010 · 16 oct: hay señales documentadas en la Bitácora; su clasificación y recuento cuantitativo no están consolidados.'}
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
 const vals=Object.values(series).flat().filter(numeric);const top=key==='signals'?Math.max(4,Math.ceil(Math.max(0,...vals)/2)*2):100;
 const Y=v=>B-v/top*plotH;const ticks=key==='signals'?[0,top/2,top]:[0,25,50,75,100];
 const latest=timeline.reduce((last,_,i)=>Object.values(series).some(a=>numeric(a[i]))?i:last,-1);
 let s='<svg class="chart-svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" role="img" aria-labelledby="'+key+'-svg-title '+key+'-svg-desc"><title id="'+key+'-svg-title">'+esc(definitions.find(x=>x.key===key).title)+'</title><desc id="'+key+'-svg-desc">Eje temporal del '+timeline[0].date+' al '+timeline[timeline.length-1].date+'. Los días sin valor quedan vacíos; no se interpolan.</desc>';
 if(latest<timeline.length-1){const start=latest<0?L:(X(latest)+X(latest+1))/2;s+='<rect class="chart-pending-area" x="'+start+'" y="'+T+'" width="'+(W-R-start)+'" height="'+plotH+'"/><text class="axis-label" x="'+((start+W-R)/2)+'" y="'+(T+16)+'" text-anchor="middle">'+(W<420?'Sin cálculo':'Sin valores recalculados')+'</text>';}
 ticks.forEach(v=>{s+='<line class="gridline" x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(v)+'" y2="'+Y(v)+'"/><text class="axis-label" x="'+(L-8)+'" y="'+(Y(v)+4)+'" text-anchor="end">'+v+'</text>'});
 s+='<line class="axis" x1="'+L+'" x2="'+(W-R)+'" y1="'+B+'" y2="'+B+'"/>';
 const stride=W<420?3:W<650?2:1;
 timeline.forEach((d,i)=>{if(i%stride&&i!==timeline.length-1)return;s+='<text class="axis-label" x="'+X(i)+'" y="'+(B+20)+'" text-anchor="'+(i===0?'start':i===timeline.length-1?'end':'middle')+'">'+esc(dateLabel(d.date))+'</text>'});
 Object.entries(series).forEach(([name,a],j)=>{
  const color=colors[j%colors.length];let seg=[];const flush=()=>{if(seg.length>1)s+='<polyline class="line-series series-'+color+'" points="'+seg.join(' ')+'"/>';seg=[]};
  a.forEach((v,i)=>{if(!numeric(v)){flush();return}const x=X(i),y=Y(v),label=name+' · '+dateLabel(timeline[i].date)+' · '+v;
   if(key==='signals'){const slot=plotW/Math.max(1,timeline.length-1),bw=Math.min(15,slot*.15),group=Object.keys(series).length*bw,center=Math.max(L+group/2,Math.min(W-R-group/2,x)),bx=center-group/2+j*bw;s+='<rect class="bar-'+color+'" x="'+bx+'" y="'+y+'" width="'+(bw*.85)+'" height="'+(B-y)+'"><title>'+esc(label)+'</title></rect>';}
   else{seg.push(x+','+y);s+='<circle class="dotpt series-'+color+'" cx="'+x+'" cy="'+y+'" r="3.5"><title>'+esc(label)+'</title></circle>';}
  });flush();
 });
 s+='</svg>';return s;
}
function card(data,def,width){
 const latest=data.timeline.reduce((last,d,i)=>Object.values(data[def.key]).some(a=>numeric(a[i]))?i:last,-1);
 const last=latest<0?'Sin valores':dateLabel(data.timeline[latest].date)+' 2026';
 const entries=Object.entries(data[def.key]);
 return '<h4>'+esc(def.title)+'</h4><p>'+esc(def.description)+'</p><p class="chart-cut"><strong>Seguimiento hasta el '+esc(dateLabel(data.cutoff))+' 2026</strong> · Últimos valores: '+esc(last)+'</p><div class="chart-wrap">'+renderChart(data,def.key,width)+'</div><div class="legend">'+entries.map(([name],i)=>'<span><i class="'+colors[i%colors.length]+'"></i>'+esc(name)+'</span>').join('')+'</div><p class="chart-note">La zona sombreada indica valores no recalculados: no significa cero ni estabilidad. Las curvas no se prolongan artificialmente.</p><p class="chart-reading">'+esc(def.reading)+'</p><details class="chart-values"><summary>Consultar valores y días pendientes</summary>'+data.timeline.map((d,i)=>'<p><strong>'+esc(d.entry+' · '+dateLabel(d.date))+'</strong> — '+esc(entries.map(([name,a])=>name+': '+(numeric(a[i])?a[i]:'sin cálculo')).join(' ; '))+'</p>').join('')+'</details>';
}
function synchronize(data,index,current){
 const known=new Map(data.timeline.map((d,i)=>[d.date,i]));const all=[...index.entradas].filter(e=>e.fecha<=current.fecha).sort((a,b)=>a.fecha.localeCompare(b.fecha));
 const out={...data,cutoff:current.fecha,timeline:all.map(e=>({date:e.fecha,entry:e.codigo}))};
 definitions.forEach(def=>out[def.key]=Object.fromEntries(Object.entries(data[def.key]).map(([k,a])=>[k,all.map(e=>known.has(e.fecha)?a[known.get(e.fecha)]??null:null)])));
 return out;
}
const api={definitions,renderChart,card,synchronize};if(typeof module!=='undefined'&&module.exports)module.exports=api;
if(typeof document==='undefined')return;
function init(){const container=document.getElementById('dashboard-temporal-charts');if(!container)return;let data=JSON.parse(document.getElementById('dashboard-chart-data').textContent);let lastWidth=0;
 function draw(){const W=Math.round(container.clientWidth)-34;if(Math.abs(W-lastWidth)<2&&lastWidth)return;lastWidth=W;container.innerHTML=definitions.map(def=>'<article class="chart-card wide" data-chart="'+def.key+'">'+card(data,def,W)+'</article>').join('')}
 draw();if(typeof ResizeObserver!=='undefined')new ResizeObserver(draw).observe(container);else window.addEventListener('resize',draw);
 Promise.all(['data/dashboard_timeseries.json','data/diario_index.json','data/current.json'].map(url=>fetch(url,{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('Datos inaccesibles');return r.json()}))).then(([fresh,index,current])=>{data=synchronize(fresh,index,current);lastWidth=0;draw();document.getElementById('dashboard-chart-sync').textContent='Gráficas sincronizadas con '+current.codigo+' · '+dateLabel(current.fecha)+' 2026. Los días sin cálculo figuran expresamente como pendientes.'}).catch(()=>{document.getElementById('dashboard-chart-sync').textContent='Versión editorial conservada · '+dateLabel(data.cutoff)+' 2026. Sincronización en directo no confirmada.'})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})(typeof globalThis!=='undefined'?globalThis:this);
