"""Sincroniza los índices visibles sin modificar entregas ni validaciones.

Desde la raíz del repositorio: python3 .github/scripts/sync_bitacora.py --write
Sin --write comprueba cobertura, orden, enlaces, títulos y pie del archivo.
"""
import argparse
import html
import json
import re
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[2] / 'sophhia-29n'


class Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.card = None
        self.heading = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'article' and 'entry' in a.get('class', '').split():
            self.card = {'code': a.get('data-entry'), 'title': '', 'links': []}
        if self.card is not None:
            if tag == 'h2':
                self.heading = True
            if tag == 'a':
                self.card['links'].append(a.get('href'))

    def handle_data(self, data):
        if self.card is not None and self.heading:
            self.card['title'] += data

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.heading = False
        if tag == 'article' and self.card is not None:
            self.cards.append(self.card)
            self.card = None


def text(fragment):
    return html.unescape(re.sub('<[^>]+>', '', fragment)).strip()


def synchronize(base, write=False):
    entries = json.loads((base / 'data/diario_index.json').read_text())['entradas']
    entries = sorted(entries, key=lambda e: e['fecha'], reverse=True)
    current = json.loads((base / 'data/current.json').read_text())
    assert entries[0]['codigo'] == current['codigo'], 'Registro y current no coinciden'
    assert len({e['codigo'] for e in entries}) == len(entries), 'Código duplicado en registro'
    path = base / 'diario/index.html'
    original = path.read_text()
    section = re.search(r'<section\b[^>]*>(.*?)</section>', original, re.S)
    assert section, 'Falta sección del archivo'
    existing = {}
    for card in re.findall(r'<article\b.*?</article>', section[1], re.S):
        match = re.search(r'D-\d{3}', text(card))
        assert match, 'Tarjeta sin código'
        assert match[0] not in existing, 'Tarjeta duplicada'
        existing[match[0]] = card
    expected = []
    for entry in entries:
        code = entry['codigo']
        target = Path(entry['url']).name
        daily = base / 'diario' / target
        assert daily.is_file(), f'No existe {daily}'
        assert code in daily.read_text(), f'Código distinto en {daily}'
        card = existing.get(code)
        if card is None:
            source = daily.read_text()
            lead = re.search(r'<p\b[^>]*class=[\"\']lead[\"\'][^>]*>(.*?)</p>', source, re.S)
            summary = text(lead[1]) if lead else ''
            date = entry['fecha'].split('-')
            month = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'][int(date[1])-1]
            label = f'{int(date[2])} de {month} de {date[0]}'
            card = (f'<article class="entry" data-entry="{code}">'
                    f'<div class="code">{code} · {label} · {html.escape(entry["estado"])}</div>'
                    f'<h2>{html.escape(entry["titulo"])}</h2>'
                    f'<p>{html.escape(summary)}</p>'
                    f'<a class="cta" href="{target}">Leer {code}</a></article>')
        # Preserva literalmente el contenido histórico de las tarjetas existentes.
        card = re.sub(r'(<article\b)([^>]*)(>)',
                      lambda m: m[1] + re.sub(r'\sdata-entry="[^"]*"', '', m[2]) + f' data-entry="{code}">' , card, count=1)
        expected.append(card)
    assert not (set(existing) - {e['codigo'] for e in entries}), 'Tarjetas fuera del registro'
    updated = original[:section.start(1)] + '\n' + '\n'.join(expected) + '\n' + original[section.end(1):]
    footer = (f'Archivo SOPHHIA 29-N · {current["codigo"]} · {current["fecha_legible"]}'
              f' · {current["hora_corte"]} · {current["timezone"]} · {current["validacion"]}.'
              ' Las validaciones anteriores mantienen sus respectivos alcances.')
    updated, count = re.subn(r'(<footer class="footer">).*?(</footer>)',
                            lambda m: m[1] + html.escape(footer) + m[2], updated, flags=re.S)
    assert count == 1, 'Pie de archivo no único'
    actual = updated if write else original
    parser = Cards()
    parser.feed(actual)
    assert len(parser.cards) == len(entries), f'{path}: {len(parser.cards)} tarjetas / {len(entries)} entradas'
    for card, entry in zip(parser.cards, entries):
        assert card['code'] == entry['codigo'], f'{path}: orden/código incorrecto: {card["code"]} / {entry["codigo"]}'
        assert card['title'].strip(), f'{path}: título vacío para {entry["codigo"]}'
        # Los históricos pueden conservar títulos editoriales abreviados.
        if entry['codigo'] == current['codigo']:
            assert card['title'].strip() == entry['titulo'], f'{path}: título vigente distinto'
        assert Path(entry['url']).name in card['links'], f'{path}: enlace incorrecto'
    assert html.escape(footer) in actual, f'{path}: pie obsoleto'
    if write:
        path.write_text(updated)
    print(f'OK {path.relative_to(ROOT)}: {len(entries)} tarjetas, {entries[0]["codigo"]} primero')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    for edition in [ROOT, ROOT / 'ciudadana']:
        synchronize(edition, args.write)
