"""Envío privado del piloto por SMTP, configurado con secretos de Actions."""
import hashlib
import json
import os
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]

def main():
    names = ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASSWORD', 'MAIL_TO')
    if not all(os.environ.get(k) for k in names):
        print('Correo no activado: faltan secretos SMTP o destinatario.')
        return
    data = json.loads((ROOT / 'public/data.json').read_text(encoding='utf-8'))
    # No enviar informes de una descarga fallida ni contenido solo de referencia.
    if data['errors'] or any(s['status'] != 'verified' or s['lag_warning'] for s in data['series'].values()):
        print('Envío omitido: hay fuentes sin validar o con rezago de actualización.')
        return
    now = datetime.now(ZoneInfo('America/Argentina/Buenos_Aires'))
    cadence = os.environ.get('MAIL_FREQUENCY', 'weekly')
    if cadence not in ('daily', 'weekly', 'monthly'):
        raise ValueError('Frecuencia no válida')
    if (cadence == 'daily' and now.weekday() > 4) or (cadence == 'weekly' and now.weekday() != 4) or (cadence == 'monthly' and now.day != 1):
        print('Hoy no corresponde un envío para la frecuencia configurada.')
        return
    period = now.strftime('%Y-%m-%d') if cadence == 'daily' else now.strftime('%G-W%V') if cadence == 'weekly' else now.strftime('%Y-%m')
    key = hashlib.sha256((cadence + period + data['fingerprint']).encode()).hexdigest()
    state_file = ROOT / 'automation-state.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    if state.get('mail_key') == key:
        print('Este informe ya fue enviado.')
        return
    msg = EmailMessage()
    msg['Subject'] = f'T+1 | Pulso económico · {now:%d/%m/%Y}'
    msg['From'] = os.environ.get('MAIL_FROM', os.environ['SMTP_USER'])
    msg['To'] = os.environ['MAIL_TO']
    blocks = ['T+1 · Piloto privado', data['report']['label']]
    for s in data['report']['sections']:
        blocks.extend([s['title'], s['fact'], s['reading'], 'Límites: ' + s['limit']])
    blocks.extend(['Fuentes y períodos:', *[f'{s["title"]}: {s["data"][-1]["date"]} · {s["url"]}' for s in data['series'].values()]])
    msg.set_content('\n\n'.join(blocks))
    with smtplib.SMTP(os.environ['SMTP_HOST'], int(os.environ.get('SMTP_PORT', '587')), timeout=30) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(os.environ['SMTP_USER'], os.environ['SMTP_PASSWORD'])
        smtp.send_message(msg)
    # Persistir antes de publicar el resultado del workflow. SMTP no ofrece exactly-once.
    state_file.write_text(json.dumps({'mail_key': key, 'sent_at': now.isoformat()}), encoding='utf-8')
    print('Informe enviado al destinatario configurado.')

if __name__ == '__main__':
    main()
