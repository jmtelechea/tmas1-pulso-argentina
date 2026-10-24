# T+1 · Pulso de la economía argentina

Piloto de consulta de inflación, actividad y tipo de cambio. Web estática, datos y cálculos reproducibles y automatización para GitHub Pages + Actions. Sin dependencias de Python externas ni recursos de terceros en el navegador.

## Operación actual con ChatGPT en la nube

GitHub Actions obtiene y valida las series y publica GitHub Pages a las 18:23 de Argentina los días hábiles. Una tarea programada de ChatGPT, `T+1 · Análisis y resumen semanal`, está configurada en la nube a las 19:00 de los mismos días. Su identificador es `6add41fa51848190a62d924fe49e8c03`; usa la zona `America/Buenos_Aires`. La programación utiliza la cuenta de ChatGPT, sujeta a sus límites; no una API facturada aparte.

La tarea lee `automation/CLOUD.md` y `public/evidence.json`, produce `public/analysis.json` y usa Gmail conectado para el envío privado. Antes de mostrar el análisis, el proceso comprueba fingerprint, fecha, secciones, hechos y períodos. Estos controles no demuestran la corrección económica de las interpretaciones. Si el análisis no corresponde a los datos, muestra lectura descriptiva.

Gmail envía una prueba inicial y luego el resumen de los viernes. La entrega y la publicación deben verificarse por sus resultados: tener una programación guardada no demuestra una ejecución exitosa. Los IDs de correo quedan en `automation/cloud-state.json`, sin publicar direcciones. Las suscripciones públicas y los productos diario/mensual no están habilitados.

El workflow ya no utiliza Gemini ni SMTP. Los scripts y las indicaciones siguientes sobre SMTP describen una alternativa anterior y no forman parte de la ejecución programada actual.

## Preparación inicial (histórico)

- Interfaz y lecturas descriptivas disponibles.
- Datos iniciales: copia de referencia de un dashboard previo del workspace, filtrada desde 2017. No se declara que sean los últimos datos publicados. La conexión a la API fue rechazada desde el entorno local durante la preparación.
- Actions intenta descargar y validar las fuentes; conserva una copia identificada si falla.
- IA no activada hasta configurar una credencial gratuita y el modelo disponible en esa cuenta.
- Correo no activado hasta configurar secretos SMTP y probar una entrega.
- No se recolectan suscripciones públicas ni se publica el correo del destinatario.

## Ejecutar y comprobar

```text
python -m unittest discover -s tests -v
python scripts/update.py
python -m http.server 8080 --directory public
```

`python scripts/update.py --offline` recalcula las lecturas con la base guardada y marca expresamente el uso de referencia local. No convierte esa base en una fuente recién verificada.

## Publicación gratuita

En Settings → Pages, seleccionar GitHub Actions. El workflow publica únicamente `public/`, sin scripts, secretos ni estado del correo. El repositorio es público para utilizar Pages en GitHub Free.

El proceso se ejecuta a las 21:23 UTC de lunes a viernes (18:23 de Argentina); GitHub puede retrasar u omitir ejecuciones programadas. También puede iniciarse manualmente. GitHub puede desactivar programaciones de repositorios públicos inactivos; el plan gratuito no garantiza operación perpetua sin mantenimiento.

## Alternativa anterior de IA (retirada del workflow)

La versión inicial contemplaba `GEMINI_API_KEY` y `GEMINI_MODEL`. La integración se reemplazó por la tarea de ChatGPT en la nube y se eliminó la llamada a Gemini. No configurar estas variables para la operación actual.

El sistema envía únicamente datos macro públicos al proveedor. La IA conserva los hechos y períodos calculados. Los controles rechazan cambios de hechos, textos incompletos y nuevas cifras en la interpretación. Es una validación limitada: no demuestra la corrección de los mecanismos económicos. Si falla, se publica lectura descriptiva identificada; no se presenta como análisis generado con IA.

## Alternativa SMTP (fuera de la operación actual)

Para Gmail, basta configurar `SMTP_USER` y `SMTP_PASSWORD`; host predeterminado `smtp.gmail.com`, puerto 587. Si `MAIL_TO` está vacío, se envía exclusivamente a la misma cuenta `SMTP_USER`. `MAIL_FROM` vacío también utiliza esa cuenta. La prueba de conexión se inicia en Actions → Actualizar y publicar piloto → Run workflow → `test_email`. Esa prueba envía un aviso de conexión, no un informe económico ni una confirmación de futuras ejecuciones. No evita los controles de calidad de los informes reales.

Guardar como secretos de Actions `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_TO` y opcionalmente `MAIL_FROM`. SMTP utiliza STARTTLS, puerto 587. No usar la contraseña normal de una cuenta personal. Si el proveedor requiere una contraseña de aplicación, su creación corresponde al titular de la cuenta.

El piloto está configurado para el resumen de los viernes. El envío omite los push y no se ejecuta si faltan secretos, hay errores de descarga o hay fuentes conservadas/con rezago excesivo. `automation-state.json` evita repetir el mismo informe en condiciones normales; SMTP no garantiza entrega exactamente una vez ante fallas entre el envío y la persistencia del estado.

Diario, semanal y mensual son frecuencias previstas. Esta primera implementación comparte la estructura del informe; una síntesis semanal/mensual histórica con criterios propios es una ampliación pendiente, no una función declarada terminada.

## Fuentes y convenciones

- IPC general: serie `145.3_INGNACUAL_DICI_M_38`, variación mensual en fracción. Se multiplica por 100 para mostrar porcentajes.
- IPC núcleo y regulados: variación mensual calculada desde los índices mediante `representation_mode=percent_change`; salida en fracción.
- EMAE desestacionalizado: `143.3_NO_PR_2004_A_31`, índice 2004=100. Variación mensual: `(nivel_t / nivel_t-1 - 1) * 100`.
- EMAE original: `143.3_NO_PR_2004_A_21`, para variaciones interanuales; no se sustituye por la serie desestacionalizada si no se obtiene.
- Mayorista: serie 5 de la API Monetarias v4 del BCRA, pesos por dólar. No representa dólar minorista ni financiero.
- Inflación interanual: `(producto(1 + variación_mensual) - 1) * 100`, últimos doce meses consecutivos. Se calcula antes de redondear.

Se rechazan fechas futuras, fechas duplicadas, valores no finitos y huecos en series mensuales. Se advierte rezago después de 50 días desde el inicio del mes IPC, 75 para EMAE y 7 desde la observación cambiaria. Son umbrales operativos; no sustituyen el calendario oficial ni aseguran detectar inmediatamente una publicación pendiente.

## Límites del piloto

No ofrece precios intradiarios, MEP/CCL, pronósticos ni atribución causal automatizada validada. No requiere mantener una computadora encendida una vez comprobada la ejecución en GitHub. El funcionamiento autónomo depende de disponibilidad de fuentes, credenciales, cuotas y políticas de los proveedores. El código no garantiza costo cero si el usuario habilita servicios con facturación.
