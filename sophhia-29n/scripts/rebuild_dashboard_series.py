#!/usr/bin/env python3
"""Rebuild audited documentary indicators. Standard library only; no network."""
from pathlib import Path
from collections import Counter
import json,hashlib,csv,io
BASE=Path(__file__).resolve().parents[1]
def load(p):return json.loads((BASE/p).read_text())
def save(p,d):(BASE/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def build():
 rule=load('data/auditoria/regla_series_v1.json');ledger=load('data/auditoria/evidencias_diarias_v1.json');index=load('data/diario_index.json');current=load('data/current.json')
 for s in rule['snapshots']:
  assert hashlib.sha256((BASE/s['path']).read_bytes()).hexdigest()==s['sha256'],f"Source snapshot changed: {s['path']}"
 rows=ledger['records'];assert len({r['id'] for r in rows})==len(rows),'Duplicate evidence ID'
 dates=sorted({r['date'] for r in rows});entries={e['fecha']:e for e in index['entradas']};assert dates[-1]==current['fecha']
 for r in rows:
  assert r['entry']==entries[r['date']]['codigo'];assert r['evidence']['entry_url']==entries[r['date']]['url']
  assert r['classification'] in ['Confirmatorias','Vigilancia','Disruptivas','Recalibradoras','contexto','metodologica','excluida']
  assert r['count_in_signals']==(r['eligible'] and r['classification'] in ['Confirmatorias','Vigilancia','Disruptivas','Recalibradoras'])
  if not r['eligible']:assert not r['variable_levels'] and not r['scenario_levels']
  assert all(isinstance(v,int) and 1<=v<=3 for v in [*r['variable_levels'].values(),*r['scenario_levels'].values()])
  assert len(r['groups'])==len(set(r['groups']))
 active=lambda date:[r for r in rows if r['date']==date and r['eligible']]
 def level(date,code,field):
  vals=[r[field][code] for r in active(date) if code in r[field]]
  return max(vals) if vals else None
 scenarios={name:[level(date,c,'scenario_levels') for date in dates] for c,name in [('G1','G1 · PP‑Vox coalición'),('G2','G2 · PP apoyo Vox'),('G4','G4 · Reconstrucción progresista'),('G5','G5 · Bloqueo/repetición')]}
 mappings=rule['mapping']; variables={k:[level(date,mappings[k],'variable_levels') for date in dates] for k in ['Vivienda','Inflación/coste de vida','Fragmentación izquierda','Relación PP‑Vox','Participación','Bloqueo']}
 territorial={k:[level(date,mappings[k],'variable_levels') for date in dates] for k in ['Agenda nacionalista catalana','Agenda nacionalista vasca','Veto/bisagra territorial','Compatibilidad programática-territorial','Agendas territoriales complementarias']}
 classes=['Confirmatorias','Vigilancia','Disruptivas','Recalibradoras'];groups=['PP‑Vox','PSOE + izquierda','Territoriales/bisagra','Garantías y procedimiento']
 signals={k:[sum(r['count_in_signals'] and r['classification']==k for r in active(date)) for date in dates] for k in classes}
 blocks={k:[sum(r['count_in_signals'] and k in r['groups'] for r in active(date)) for date in dates] for k in groups}
 statuses={e['fecha']:e['estado'] for e in index['entradas']}
 result={'version':'v0.28-auditada-reconstruccion-v1','mode':'Reconstrucción documental retrospectiva: estados ordinales y recuentos. Codificación IA pendiente IH; no probabilidades ni pesos MICMAC.','method':'REG-SERIES-29N-001','cutoff':current['fecha'],'current_entry':current['codigo'],'last_numeric_date':dates[-1],'updated':'2026-10-16','reconstruction_date':'2026-10-16','interpretation_cutoff':'2026-10-16T12:25:00+02:00','missing_value_policy':'null = sin codificación sustentada; 0 sólo en recuentos y significa cero unidades codificadas en la ficha','timeline':[{'date':date,'entry':entries[date]['codigo'],'source_status':statuses[date],'retrospective':True} for date in dates], 'scenarios':scenarios,'blocks':blocks,'variables':variables,'territorial':territorial,'signals':signals,'metric_types':{'scenarios':'ordinal_1_3','blocks':'counts','variables':'ordinal_1_3','territorial':'ordinal_1_3','signals':'counts'},'method_url':'metodo/auditoria-series-2026-10-16.html','evidence_url':'data/auditoria/evidencias_diarias_v1.json','validation':'Reconstrucción editorial pendiente de validación IH específica','legacy_archive':'data/auditoria/series_anteriores_v027.json','comparability_warning':'La nueva serie se reconstruye desde el 7 con la misma regla. No empalmar con las antiguas puntuaciones 0–100.','note':'Sin recalibración de A-000, sin modificación de MICMAC ni de probabilidades selladas.'}
 save('data/dashboard_timeseries.json',result)
 # Explicit per-value provenance and coverage audit.
 provenance=[]
 fieldmap={'scenarios':('scenario_levels',{'G1 · PP‑Vox coalición':'G1','G2 · PP apoyo Vox':'G2','G4 · Reconstrucción progresista':'G4','G5 · Bloqueo/repetición':'G5'}),'variables':('variable_levels',mappings),'territorial':('variable_levels',mappings)}
 for group in ['scenarios','blocks','variables','territorial','signals']:
  for label,vals in result[group].items():
   for i,date in enumerate(dates):
    if group in fieldmap:
     field,codes=fieldmap[group];ids=[r['id'] for r in active(date) if codes[label] in r[field]]
    elif group=='blocks':ids=[r['id'] for r in active(date) if r['count_in_signals'] and label in r['groups']]
    else:ids=[r['id'] for r in active(date) if r['count_in_signals'] and r['classification']==label]
    provenance.append({'date':date,'entry':entries[date]['codigo'],'group':group,'series':label,'value':vals[i],'evidence_ids':ids,'status':result['validation']})
 save('data/auditoria/trazabilidad_valores_v1.json',{'method':rule['id'],'values':provenance})
 report={'code':'AUD-SERIES-29N-20261016','scope':'Base 7–10 y reconstrucción 11–16','status':'Auditoría documental realizada; nueva codificación pendiente IH','evidence_records':len(rows),'external_units_counted':sum(r['count_in_signals'] for r in rows),'excluded_records':[{'id':r['id'],'reason':r['reason']} for r in rows if not r['eligible']],'legacy_origin':[{'commit':'179163021f4eb497dca1439ceb22d4d840007365','date':'2026-10-09','finding':'Primera incorporación de arrays con puntuaciones literales; no consta función de derivación por señal.'},{'commit':'4325811618df404a41d1486f0c93a8af9fa7da2f','date':'2026-10-10','finding':'Extensión con D-004; no consta regla reproducible para el salto de cada puntuación.'}],'findings':['Las puntuaciones antiguas son reproducibles como lectura de un JSON, pero no derivables de sus evidencias con una fórmula documentada. No se certifica su validez cuantitativa.','Los recuentos antiguos mezclan ámbitos y no documentan la asignación de clases. Se rehacen los diez días con la misma taxonomía.','Los códigos del CSV del 8 se remapean por significado al inventario canónico; originales intactos.','D-005 contiene duplicación temática: se fusionan vivienda 01/02 y ventaja/sondeos 03/04.','D-008 excluye IPC definitivo por hora de publicación no acreditada; D-009 excluye dos enlaces genéricos.','No hay observación sustentada de agenda vasca en este registro: se muestra sin datos, no constante.','La puntuación de atención de una variable no es su intensidad en el mundo ni un peso de MICMAC.','Las aprobaciones históricas no validan retrospectivamente la regla nueva ni su codificación.'],'daily':[{'date':date,'entry':entries[date]['codigo'],'source_status':statuses[date],'total_records':sum(r['date']==date for r in rows),'counted':sum(r['date']==date and r['count_in_signals'] for r in rows),'excluded':sum(r['date']==date and not r['eligible'] for r in rows),'signals':{k:signals[k][i] for k in classes},'scenarios':{k:scenarios[k][i] for k in scenarios}} for i,date in enumerate(dates)],'limitations':rule['limitations']}
 save('data/auditoria/informe_auditoria_v1.json',report)
 output=io.StringIO();writer=csv.writer(output);writer.writerow(['fecha','entrada','caja','serie','valor','evidencias','estado'])
 for p in provenance:writer.writerow([p['date'],p['entry'],p['group'],p['series'],'' if p['value'] is None else p['value'],';'.join(p['evidence_ids']),p['status']])
 (BASE/'data/auditoria/seguimiento_reconstruido_v1.csv').write_text(output.getvalue())
 return result,report
if __name__=='__main__':
 result,report=build();print(json.dumps({'method':result['method'],'records':report['evidence_records'],'counted':report['external_units_counted'],'reconstructed_through':result['cutoff']},ensure_ascii=False))
