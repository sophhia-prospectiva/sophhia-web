/* Public presentation synchronisation. D-014: grid and editorial labels; scoring rules unchanged. */
(function(){
'use strict';
if(typeof document==='undefined'){
  if(typeof module!=='undefined'&&module.exports)module.exports=require('./dashboard-charts-v0.29.js');
  return;
}
const own=document.currentScript;
const scriptURL=new URL(own&&own.src?own.src:'assets/dashboard-charts.js',document.baseURI);
const dataURL=new URL('../data/',scriptURL);
const core=document.createElement('script');
const rendererURL=new URL('dashboard-charts-v0.29.js',scriptURL);
rendererURL.search=scriptURL.search;
core.src=rendererURL.href;
core.async=false;
core.onerror=function(){const n=document.getElementById('dashboard-chart-sync');if(n)n.textContent='No se ha podido cargar el visor de gráficas. Los registros permanecen disponibles en la Bitácora.';};
document.head.appendChild(core);
function text(id,value){const node=document.getElementById(id);if(node)node.textContent=value==null?'':String(value);}
function link(id,path,label){const node=document.getElementById(id);if(node){node.href=path;node.textContent=label;}}
function element(tag,value,cls){const node=document.createElement(tag);if(cls)node.className=cls;if(value!=null)node.textContent=value;return node;}
function validPath(path){return typeof path==='string'&&/^diario\/\d{4}-\d{2}-\d{2}\.html$/.test(path);}
function render(c,d,index){
  if(!c||!/^D-\d{3}$/.test(c.codigo||'')||!/^\d{4}-\d{2}-\d{2}$/.test(c.fecha||'')||!validPath(c.url)||!String(c.estado_publicacion||'').startsWith('publicada_'))throw Error('Estado vigente inválido');
  if(!d||d.current_entry!==c.codigo||d.updated!==c.fecha||!index||!Array.isArray(index.entradas))throw Error('Ediciones no sincronizadas');
  const dated=c.codigo+' · '+c.fecha_legible;
  const cut='Corte: '+c.fecha+' · '+c.hora_corte+' · Europe/Madrid. '+c.validacion;
  text('dash-current-badge',dated+' · '+c.validacion);
  text('dash-current-title',c.fecha_legible+' · '+c.titulo);
  text('dash-current-summary',c.resumen);
  text('dash-current-cut',cut);
  link('dash-current-link',c.url,'Leer '+c.codigo);
  text('dash-current-heading','Estado del sistema '+c.codigo+' · '+c.validacion);
  text('dash-core-reading',d.system_state);
  text('dash-current-entry',dated);
  text('dash-where-heading',c.codigo+' · Estado vigente');
  text('dash-where-summary',c.resumen);
  text('dash-journey-heading','D-001 → '+c.codigo);
  text('sophhia-current-status',dated+' · '+c.validacion);
  text('sophhia-current-title',c.titulo);
  text('sophhia-current-summary',c.resumen);
  text('sophhia-current-decision',c.decision);
  link('sophhia-current-link',c.url,'Leer '+c.codigo);
  text('sophhia-sync-note','Estado editorial sincronizado: '+dated+'. Sin recalibración automática de A-000 ni MICMAC.');
  document.querySelectorAll('.metric').forEach(function(n){const k=n.querySelector('.k');if(k&&k.textContent.trim()==='Actualización'){const v=n.querySelector('.n'),l=n.querySelector('.l');if(v)v.textContent=c.codigo;if(l)l.textContent=c.fecha_legible+' · '+c.validacion;}});
  const where=document.querySelector('#dash-where-now ul');
  if(where&&Array.isArray(d.current_bullets)){where.replaceChildren();d.current_bullets.forEach(function(v){where.appendChild(element('li',v));});}
  const heading=document.getElementById('dash-journey-heading');
  const history=heading&&heading.closest('article')?heading.closest('article').querySelector('ul'):null;
  if(history){history.replaceChildren();index.entradas.slice().sort(function(a,b){return a.fecha.localeCompare(b.fecha);}).forEach(function(e){const li=element('li',e.codigo+' · '+e.titulo+' ('+e.fecha+'; '+e.estado.replaceAll('_',' ')+')');history.appendChild(li);});}
  const old=document.getElementById('sophhia-previous-card');
  const previous=c.anterior;
  if(old&&previous&&validPath(previous.url)){
    const a=element('a','Leer '+previous.codigo+' · histórico','cta secondary');a.href=previous.url;
    old.replaceChildren(element('span','Histórico · '+previous.codigo+' · '+previous.fecha_legible,'pill info'),element('h3',previous.titulo),element('p',previous.estado+'. Se conserva su propio corte informativo; no se extiende la validación de otras entradas.'),a);
  }
  const currentCard=document.getElementById('dash-current-card');
  if(currentCard&&!document.getElementById('dash-demoscopy-register')){
    const p=element('p',null,'micro');p.id='dash-demoscopy-register';
    const a=element('a','Consultar la comparación y las reservas de verificación');a.href=c.url+'#comparacion';p.appendChild(a);currentCard.appendChild(p);
  }
  document.body.dataset.currentEntry=c.codigo;
  document.body.dataset.editorialCutoff=(c.ventana_novedades&&c.ventana_novedades.hasta_inclusivo)||c.fecha;
}
function start(){
  Promise.all(['current.json','dashboard.json','diario_index.json'].map(function(path){return fetch(new URL(path,dataURL).href,{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('Datos no accesibles');return r.json();});})).then(function(items){render(items[0],items[1],items[2]);}).catch(function(){text('sophhia-sync-note','No se ha podido confirmar la sincronización completa. Las fichas estáticas conservan su fecha; consulte la Bitácora para comprobar la última publicación.');});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();

