"""Importación explícita de una copia local previa, sin declararla descarga nueva."""
import argparse
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
spec = importlib.util.spec_from_file_location('updater', Path(__file__).with_name('update.py'))
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)
raw = json.loads(args.source.read_text(encoding='utf-8'))
bycode = {s['code']: s for s in raw['series']}
series = {}
for key, code in [('ipc', 'P1'), ('nucleo', 'P2'), ('regulados', 'P3'), ('emae', 'A2'), ('dolar', 'BANDAS_FX')]:
    original = bycode[code]
    if key == 'dolar':
        points = next(line['data'] for line in original['lines'] if 'mayorista' in line['label'].lower())
    else:
        points = original['data']
    points = [dict(p) for p in points if '2017-01-01' <= p['date'] <= '2026-10-24']
    u.validate(points, key)
    sid, title, unit, source, frequency = u.SPECS[key]
    url = ('https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/5' if key == 'dolar' else
           'https://apis.datos.gob.ar/series/api/series?ids=' + sid)
    series[key] = {'id': sid, 'title': title, 'unit': unit, 'source': source,
        'frequency': frequency, 'url': url, 'status': 'reference',
        'checked_at': None, 'reference_snapshot_at': raw['updated_at'],
        'description': title, 'data': points}
u.OUT.parent.mkdir(parents=True, exist_ok=True)
u.OUT.write_text(json.dumps({'series': series}, ensure_ascii=False), encoding='utf-8')
print('Copia de referencia importada. No sustituye la comprobación de la fuente en línea.')
