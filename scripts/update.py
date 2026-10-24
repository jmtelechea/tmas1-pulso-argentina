"""Fuentes oficiales, controles y lectura descriptiva. Sin dependencias externas."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import time
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'data.json'
SPECS = {
    'ipc': ('145.3_INGNACUAL_DICI_M_38', 'IPC nacional', 'fraction', 'INDEC', 'month'),
    'nucleo': ('148.3_INUCLEONAL_DICI_M_19', 'IPC núcleo', 'fraction', 'INDEC', 'month'),
    'regulados': ('148.3_IREGULANAL_DICI_M_22', 'IPC regulados', 'fraction', 'INDEC', 'month'),
    'emae': ('143.3_NO_PR_2004_A_31', 'EMAE desestacionalizado', 'index', 'INDEC', 'month'),
    'emae_original': ('143.3_NO_PR_2004_A_21', 'EMAE original', 'index', 'INDEC', 'month'),
    'dolar': ('5', 'Dólar mayorista de referencia', 'ars_usd', 'BCRA', 'day'),
}

def get_json(url, body=None, headers=None):
    req = Request(url, data=body, headers={
        'User-Agent': 'Mozilla/5.0 Tmas1-Pulso/1.0', 'Accept': 'application/json',
        **(headers or {})})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=35) as response:
                return json.load(response)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def validate(points, key):
    if len(points) < 13:
        raise ValueError('Historia insuficiente')
    previous = ''
    for p in points:
        d, v = p['date'], p['value']
        date.fromisoformat(d)
        if d > date.today().isoformat() or d <= previous:
            raise ValueError('Fechas futuras, duplicadas o desordenadas')
        if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
            raise ValueError('Valor no numérico o no finito')
        if key in ('emae', 'emae_original', 'dolar') and v <= 0:
            raise ValueError('Nivel no positivo')
        if key in ('ipc', 'nucleo', 'regulados') and not -1 < v < 10:
            raise ValueError('Variación fuera del dominio admisible')
        previous = d
    if SPECS[key][4] == 'month':
        for a, b in zip(points, points[1:]):
            da, db = date.fromisoformat(a['date']), date.fromisoformat(b['date'])
            if db.year * 12 + db.month - da.year * 12 - da.month != 1:
                raise ValueError('Serie mensual con huecos')
    return points

def download(key):
    sid, title, unit, source, frequency = SPECS[key]
    if key == 'dolar':
        url = 'https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/5?' + urlencode({'limit': 1000})
        raw = get_json(url)
        block = raw['results'][0]
        catalog = get_json('https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias')
        metadata = next(r for r in catalog['results'] if r.get('idVariable') == 5)
        description = metadata['descripcion']
        if (block.get('idVariable') != 5 or 'mayorista' not in description.lower()
                or 'pesos' not in metadata.get('unidadExpresion', '').lower()
                or metadata.get('periodicidad') != 'D'):
            raise ValueError('Metadatos cambiarios inesperados')
        points = [{'date': p['fecha'], 'value': p['valor']} for p in block['detalle'] if p.get('valor') is not None]
        points.sort(key=lambda p: p['date'])
    else:
        query = {'ids': sid, 'last': 180, 'metadata': 'full'}
        if key in ('nucleo', 'regulados'):
            query['representation_mode'] = 'percent_change'
        url = 'https://apis.datos.gob.ar/series/api/series?' + urlencode(query)
        raw = get_json(url)
        field = raw['meta'][1]['field']
        description = field.get('description', title)
        if not raw.get('data') or field.get('id', sid) != sid:
            raise ValueError('Serie o metadatos inesperados')
        reported_units = field.get('units', '')
        if key == 'ipc' and reported_units and not any(t in reported_units.lower() for t in ('porcent', 'intermensual')):
            raise ValueError('Unidad IPC inesperada: revisar conversión')
        points = [{'date': row[0][:10], 'value': row[1]} for row in raw['data'] if row[1] is not None]
    validate(points, key)
    return {'id': sid, 'title': title, 'unit': unit, 'source': source,
            'frequency': frequency, 'url': url, 'description': description,
            'checked_at': datetime.now(timezone.utc).isoformat(), 'status': 'verified', 'data': points}

def change(points, n=1):
    return (points[-1]['value'] / points[-1-n]['value'] - 1) * 100

def compound(points):
    return (math.prod(1 + p['value'] for p in points) - 1) * 100

def fmt(n):
    return f'{n:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')

def make_report(series):
    ipc, emae, fx = [series.get(k) for k in ('ipc', 'emae', 'dolar')]
    sections = []
    if ipc:
        p = ipc['data']; monthly = p[-1]['value'] * 100
        delta = (p[-1]['value'] - p[-2]['value']) * 100
        sections.append({'topic': 'inflacion', 'title': 'El ritmo de los precios', 'period': p[-1]['date'],
            'fact': f'El IPC nacional varió {fmt(monthly)}% mensual en {p[-1]["date"][:7]}. La diferencia frente al mes anterior fue de {fmt(delta)} puntos porcentuales. La variación compuesta de doce meses fue de {fmt(compound(p[-12:]))}%.',
            'reading': 'Una menor tasa mensual implica que los precios suben más despacio; no significa que hayan bajado. Para evaluar la extensión del movimiento, conviene comparar el nivel general con núcleo y regulados en el mismo mes.',
            'limit': 'Estos indicadores describen el movimiento de precios. Por sí solos no identifican cuánto corresponde a demanda, costos o tipo de cambio.'})
    if emae:
        p = emae['data']; v = change(p)
        sections.append({'topic': 'actividad', 'title': 'La dirección de la actividad', 'period': p[-1]['date'],
            'fact': f'El EMAE desestacionalizado registró {fmt(p[-1]["value"])} puntos (2004=100) en {p[-1]["date"][:7]}, con una variación mensual de {fmt(v)}%.',
            'reading': 'La serie desestacionalizada permite comparar meses consecutivos. La comparación interanual debe hacerse con la serie original y puede mostrar un movimiento distinto por el nivel de partida.',
            'limit': 'Un mes aislado no establece una tendencia. El EMAE es preliminar y puede revisarse; no se interpreta como una medida del bienestar.'})
    if fx:
        p = fx['data']
        sections.append({'topic': 'cambio', 'title': 'El movimiento del dólar oficial', 'period': p[-1]['date'],
            'fact': f'El tipo de cambio mayorista de referencia fue de $ {fmt(p[-1]["value"])} por dólar el {p[-1]["date"]}, con una variación de {fmt(change(p))}% frente a la observación anterior.',
            'reading': 'Esta cotización corresponde al mercado oficial mayorista. Un aumento expresa una depreciación nominal del peso frente al dólar en ese mercado.',
            'limit': 'No representa al dólar minorista, MEP ni CCL. Tampoco permite concluir por sí solo si hay apreciación real: eso requiere comparar precios de períodos compatibles.'})
    return {'kind': 'descriptive', 'label': 'Lectura automática con reglas verificables', 'sections': sections}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    previous = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'series': {}}
    series, errors = {}, []
    if args.offline:
        series = previous['series']
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            tasks = {pool.submit(download, key): key for key in SPECS}
            for future in concurrent.futures.as_completed(tasks):
                key = tasks[future]
                try:
                    series[key] = future.result()
                except Exception as exc:
                    errors.append(f'{key}: descarga o validación fallida ({type(exc).__name__})')
                    if key in previous['series']:
                        series[key] = {**previous['series'][key], 'status': 'cached'}
    for key, item in series.items():
        validate(item['data'], key)
        age = (date.today() - date.fromisoformat(item['data'][-1]['date'])).days
        item['age_days'] = age
        item['lag_warning'] = age > (7 if key == 'dolar' else 75 if key.startswith('emae') else 50)
    base = make_report(series)
    fingerprint = hashlib.sha256(json.dumps({k:s['data'] for k,s in sorted(series.items())},sort_keys=True).encode()).hexdigest()
    report = base
    note = 'La lectura descriptiva se reemplaza por el análisis de la tarea en la nube cuando coincide con estos datos y supera los controles.'
    cloud_file = OUT.parent / 'analysis.json'
    if cloud_file.exists() and not args.offline:
        try:
            cloud = json.loads(cloud_file.read_text(encoding='utf-8'))
            validate_cloud(cloud, fingerprint, base)
            report = {'kind': 'ai', 'label': 'Análisis de ChatGPT en la nube · sin revisión humana',
                      'sections': cloud['sections']}
            note = 'Análisis automático de ChatGPT. Los datos tienen períodos distintos y pueden tener rezago; las hipótesis no prueban causalidad.'
        except (ValueError, KeyError, TypeError):
            note = 'El análisis en la nube todavía no corresponde a esta versión de los datos o no superó los controles. Se muestra lectura descriptiva.'
    payload = {'generated_at': datetime.now(timezone.utc).isoformat(), 'fingerprint': fingerprint,
        'series': series, 'errors': errors, 'report': report, 'note': note,
        'pilot': {'email_active': False, 'subscription_open': False}}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(OUT)
    evidence = {'fingerprint': fingerprint, 'generated_at': payload['generated_at'],
        'errors': errors, 'base_report': base,
        'series': {k:{**{a:v for a,v in s.items() if a != 'data'}, 'data':s['data'][-24:]}
                   for k,s in series.items()}}
    (OUT.parent / 'evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'series': len(series), 'errors': errors, 'report_kind': report['kind']}, ensure_ascii=True))
    if not series:
        raise SystemExit('No hay datos válidos para publicar')

def validate_cloud(cloud, fingerprint, base):
    if cloud.get('fingerprint') != fingerprint:
        raise ValueError('El análisis no corresponde a estos datos')
    stamp = datetime.fromisoformat(cloud['generated_at'].replace('Z', '+00:00'))
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    if not 0 <= age <= 7 * 86400:
        raise ValueError('Fecha de generación inválida o análisis vencido')
    if len(cloud.get('sections', [])) != len(base['sections']):
        raise ValueError('Análisis incompleto')
    for actual, expected in zip(cloud['sections'], base['sections']):
        if any(actual.get(k) != expected[k] for k in ('topic', 'period', 'fact')):
            raise ValueError('Los hechos o períodos fueron modificados')
        for key in ('title', 'reading', 'limit'):
            value = actual.get(key)
            if not isinstance(value, str) or not 5 <= len(value) <= 1800 or any(c.isdigit() for c in value):
                raise ValueError('Texto interpretativo no válido')

if __name__ == '__main__':
    main()
