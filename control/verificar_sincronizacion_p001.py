#!/usr/bin/env python3
"""Control P001-CWS-001; solo lectura, sin dependencias externas.
Uso: python3 sophhia-29n/control/verificar_sincronizacion_p001.py [directorio sophhia-29n]
"""
import json,re,sys
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.hrefs=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            h=dict(attrs).get('href')
            if h:self.hrefs.append(h)

def main():
    base=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent.parent
    problems=[]; warnings=[]; good=[]
    def fail(x): problems.append(x)
    def warn(x): warnings.append(x)
    def check(x,label): (good if x else problems).append(label if x else 'FALLO: '+label)
    def file(rel):
        p=base/rel
        if not p.is_file():fail('Falta '+rel);return ''
        return p.read_text(encoding='utf-8')
    def doc(rel):
        try:return json.loads(file(rel))
        except (json.JSONDecodeError,UnicodeDecodeError) as e:fail('JSON inválido '+rel+': '+str(e));return {}
    current=doc('data/current.json'); dashboard=doc('data/dashboard.json'); diary=doc('data/diario_index.json')
    code=current.get('codigo',''); date=current.get('fecha',''); decision=current.get('decision_id','')
    url=current.get('url',''); state=current.get('estado_publicacion','')
    check(bool(re.fullmatch(r'D-\d{3}',code)),'Código de entrada diario válido')
    try: datetime.strptime(date,'%Y-%m-%d');validdate=True
    except ValueError:validdate=False
    check(validdate,'Fecha de corte válida')
    check(current.get('timezone')=='Europe/Madrid','Huso horario Europe/Madrid')
    check(bool(current.get('hora_corte')),'Hora de corte declarada')
    check(bool(decision),'Decisión IH referenciada en current.json')
    check('provisional' in str(current.get('validacion','')).lower(),'Estado provisional explícito')
    check('provisional' in state.lower(),'Estado de publicación provisional explícito')
    check(dashboard.get('current_entry')==code,'Dashboard y current coinciden en entrada')
    check(dashboard.get('updated')==date,'Dashboard y current coinciden en fecha')
    check(decision in dashboard.get('human_validation',''),'Dashboard muestra la decisión IH')
    entries=diary.get('entradas',[])
    if entries:
        head=entries[0]
        check(head.get('codigo')==code and head.get('fecha')==date,'Última entrada del índice coincide con registro vigente')
        check(head.get('decision')==decision,'Última entrada registra la decisión IH')
        check('provisional' in head.get('estado','').lower(),'Índice refleja carácter provisional')
        codes=[e.get('codigo') for e in entries]
        check(len(codes)==len(set(codes)),'Sin códigos duplicados en Bitácora')
        check(codes==sorted(codes,reverse=True),'Bitácora en orden decreciente')
        for e in entries:
            rel=e.get('url','')
            # data/diario_index.json define rutas desde sophhia-29n
            if not rel or not (base/rel).is_file():fail('Entrada sin archivo: '+str(rel))
    else: fail('Índice sin entradas')
    check(bool(url) and (base/url).is_file(),'Entrada vigente existe en '+url)
    page=file('index.html'); journal=file('diario/index.html'); explorer=file('explorador/index.html')
    present=file(url) if url else ''
    # Dashboard: el control no debe aceptar un código viejo en una ficha vigente.
    from html.parser import HTMLParser
    class DashboardScan(HTMLParser):
        def __init__(self):
            super().__init__();self.in_dashboard=False;self.depth=0;self.region=None;self.stack=[];self.parts={};self.links={}
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs);id=attrs.get('id','');
            if id=='dashboard':self.in_dashboard=True;self.depth=1
            elif self.in_dashboard:self.depth+=1
            if self.in_dashboard:
                if id.startswith('dash-current-') or id.startswith('dash-where-') or id.startswith('dash-journey-'):self.region=id;self.parts[id]='';self.stack.append((id,self.depth))
                if tag=='a' and id=='dash-current-link':self.links[id]=attrs.get('href','')
        def handle_data(self,d):
            if self.in_dashboard and self.region:self.parts[self.region]+=d
        def handle_endtag(self,tag):
            if self.in_dashboard:
                if self.stack and self.stack[-1][1]==self.depth:self.stack.pop();self.region=self.stack[-1][0] if self.stack else None
                self.depth-=1
                if self.depth==0:self.in_dashboard=False
    scan=DashboardScan();scan.feed(page)
    required=['dash-current-badge','dash-current-title','dash-current-summary','dash-current-heading','dash-current-entry','dash-where-heading','dash-where-summary','dash-current-link']
    check(all(k in scan.parts for k in required),'Dashboard tiene todos los campos actuales identificados')
    check(code in scan.parts.get('dash-current-badge',''),'Dashboard visual: código vigente en ficha principal')
    check(decision in scan.parts.get('dash-current-badge',''),'Dashboard visual: decisión IH vigente')
    check(code in scan.parts.get('dash-current-heading',''),'Dashboard visual: encabezado estado actual')
    check(code in scan.parts.get('dash-current-entry',''),'Dashboard visual: entrada vigente')
    check(code in scan.parts.get('dash-where-heading',''),'Dashboard visual: dónde estamos')
    check(scan.links.get('dash-current-link')==url,'Dashboard visual: enlace a entrada vigente')
    check('dash-live-sync' in page and 'dashboard.json' in page,'Dashboard: sincronizador dinámico instalado')
    check(code in page,'Portada identifica entrada vigente')
    check(code in journal,'Bitácora identifica entrada vigente')
    check(decision in present,'Entrada vigente identifica decisión IH')
    check(decision in page,'Portada identifica decisión IH')
    check('current.json' in page,'Portada consulta registro central')
    check('current.json' in explorer,'Explorador consulta registro central')
    check('todayLabel' in explorer,'Cono dispone de rótulo dinámico de fecha')
    # Se admiten dos implementaciones: patrón SVG o retícula generada por JavaScript.
    has_svg_pattern = bool(re.search(r'<pattern\b', explorer, re.I))
    has_dynamic_grid = (bool(re.search(r'id=[\"\']gridMinor[\"\']', explorer))
                        and bool(re.search(r'getElementById\([\"\']gridMinor[\"\']\)', explorer))
                        and 'grid-major' in explorer and 'grid-minor' in explorer
                        and bool(re.search(r'el\([\"\']line[\"\']', explorer)))
    check(has_svg_pattern or has_dynamic_grid,'Cono dispone de retícula SVG')
    check('Modelo experimental' in explorer or 'modelo experimental' in explorer.lower(),'Advertencia experimental del Explorador')
    # Evitar falsos positivos: solo comprobar enlaces internos explícitos de entrada vigente
    for html,name in [(page,'Portada'),(journal,'Bitácora')]:
        links=Links();links.feed(html)
        check(any(url.endswith(h.lstrip('./')) for h in links.hrefs),name+' enlaza entrada vigente')
    if dashboard.get('recalibration') not in ('No',False,'no'):
        warn('Dashboard registra recalibración: requiere expediente y validación cuantitativa por separado')
    # No validar la hora exacta de fuentes a partir de textos; control documental IH
    for f in current.get('fuentes_temporales',[]):
        if 'pendiente' in str(f.get('estado','')).lower() or 'contrast' in str(f.get('hora','')).lower():
            warn('Fuente con reserva temporal: '+f.get('medio','sin medio'))
    print('P001-CWS-001 | '+(code or '?')+' | '+(date or '?'))
    print('BASE:',base)
    print('PASS:',len(good),'| AVISOS:',len(warnings),'| FALLOS:',len(problems))
    for p in problems:print('ERROR:',p)
    for w in warnings:print('AVISO:',w)
    print('RESULTADO:', 'STOP PUBLICACIÓN' if problems else 'GO TÉCNICO CON RESERVAS' if warnings else 'GO TÉCNICO')
    print('NOTA: GO técnico no sustituye validación IH ni prueba visual/móvil ni contraste en GitHub Pages.')
    return 1 if problems else 0
if __name__=='__main__':raise SystemExit(main())
