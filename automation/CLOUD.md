# Operación de T+1 con ChatGPT en la nube

## Alcance autorizado

Actualizá el análisis de inflación, actividad y tipo de cambio del piloto. Usá las conexiones de GitHub y Gmail del usuario. No necesitás un entorno local, Gemini, API keys ni contraseñas SMTP. No atribuyas tus textos como opiniones personales de Juan Manuel Telechea. No cambies código, permisos ni configuración del repositorio durante las ejecuciones rutinarias.

Repositorio único: `jmtelechea/tmas1-pulso-argentina`, rama `main`. Sitio: https://jmtelechea.github.io/tmas1-pulso-argentina/

## Cada ejecución

1. Leé este archivo desde GitHub y `public/evidence.json` en la rama actual. Son datos macro públicos exportados por el proceso de datos oficial. No leas el archivo grande `public/data.json` salvo que necesites verificar una discrepancia. `base_report.sections` contiene los hechos y períodos calculados; `series` aporta observaciones, unidades, fuentes y advertencias de rezago.
2. Leé `public/analysis.json` y `automation/cloud-state.json` si existen. Un 404 significa archivo aún no creado, no permiso para inventar su SHA. Usá create_file para el primero y update_file con el SHA recién leído para reemplazos. Conservá estados de envíos ya registrados. Antes de escribir, volvé a leer evidence.json; si cambió su fingerprint, rehacé el análisis con los datos actuales.
3. Separá hechos comprobados, mecanismos plausibles y límites. Las fechas de referencia son distintas: no describas todas las observaciones como contemporáneas. Si hay lag_warning, aclaralo en el tema correspondiente. No inventes datos ni noticias y no transformes una correlación en explicación causal. No hagas pronósticos ni recomendaciones de inversión. Un análisis puede explicar qué información falta para distinguir hipótesis.
4. Escribí `public/analysis.json` con esta estructura: `{"fingerprint":"copiar de evidence","generated_at":"fecha y hora UTC ISO 8601 reales","sections":[...]}`. Cada sección conserva exactamente `topic`, `period` y `fact` del informe base. Podés mejorar `title`, `reading` y `limit`: textos entre 5 y 1800 caracteres cada uno, sin dígitos ni nuevas cifras. Tres secciones en el orden del informe base. No agregues Markdown ni HTML dentro del JSON. El cuerpo interpretativo será moderadamente breve, en castellano rioplatense. Si falta evidencia válida para algún tema, explicitá la limitación sin completar cifras. Si faltan temas obligatorios o hay errores de descarga, no publiques un análisis que parezca actualizado: notificá el problema y conservá la versión válida.
5. Un commit de analysis.json dispara GitHub Actions, que verifica hechos, períodos y correspondencia de datos antes de publicar. Confirmá el commit y la ejecución. Si existe un análisis con el mismo fingerprint, menos de siete días y sin cambios necesarios, no vuelvas a escribirlo solo para cambiar la fecha. No afirmes que se publicó hasta verificar el despliegue y que la web usa el análisis correspondiente. Si hay fallas, informá cuál sin intentar cambiar permisos.

## Envío privado

El destinatario figura en la tarea programada, no debe escribirse en archivos públicos. Usá la conexión Gmail; no pidas contraseñas. Enviá un correo de prueba en la primera ejecución si la tarea lo pide, identificado como prueba y con los períodos/rezagos visibles. Luego, solo los viernes, un resumen de los tres temas con asunto `T+1 | Pulso económico semanal`. Cada tema incluye hechos, lectura y límites, y enlaces a fuentes y sitio. No lo presentes como una revisión humana. No envíes un informe con errores de descarga; un rezago de una fuente recién consultada debe advertirse claramente, y no se describe como novedad del día.

Consultá `automation/cloud-state.json` antes de enviar. Registrá allí únicamente `test_sent_at`, `test_message_id`, `weekly_period`, `weekly_message_id` y fechas, sin direcciones ni credenciales. Tras confirmar un envío, persistí su ID para reducir duplicados. Si se envía pero falla el registro, reportalo y no reintentes el envío en la misma ejecución. Gmail más GitHub no ofrecen una transacción de entrega exactamente una vez.

No envíes correos diarios en este piloto. No publiques tuits, no abras suscripciones ni contactes a terceros. Mantenerse en silencio en ejecuciones sin cambios; avisar por el canal de la tarea solo ante una falla, una acción requerida o una modificación relevante.
