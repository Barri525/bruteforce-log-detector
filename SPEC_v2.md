# Especificación v2: base de datos y panel

## Objetivo
Ampliar el detector para guardar los intentos fallidos en una base de datos SQL y mostrar los resultados en un panel con gráficos.

## Componentes
- `detector.py`: sin cambios en su uso actual.
- `almacen.py` (nuevo): guarda y consulta los intentos en SQLite.
- `panel.py` (nuevo): genera `panel.html` a partir de la base de datos.

## Base de datos
Archivo SQLite (por defecto `datos.db`) con la tabla `intentos`:

| Columna | Tipo | Contenido |
|---|---|---|
| id | entero | identificador automático |
| archivo | texto | nombre del log de origen |
| numero_linea | entero | línea dentro del log |
| momento | texto | fecha y hora tal como aparecen en el log |
| ip | texto | IP de origen |
| usuario | texto | usuario probado |

Restricción: la pareja (`archivo`, `numero_linea`) es única, para que importar dos veces el mismo log no duplique datos.

## Uso esperado
```
python almacen.py importar auth.log
python almacen.py resumen
python panel.py
```

## Consultas del resumen
- Total de intentos fallidos
- Top 10 de IPs por número de intentos
- Top 10 de usuarios más probados
- Intentos por hora del día

## Panel (`panel.html`)
- Un solo archivo HTML, sin dependencias externas, que se abre sin internet.
- Tarjetas con el total de intentos, de IPs distintas y de usuarios distintos.
- Gráficos de barras: top de IPs, top de usuarios e intentos por hora.
- Las IPs se muestran con el último número oculto (por ejemplo `183.62.140.xxx`).

## Criterios de éxito
- Con `OpenSSH_2k.log` la base contiene 520 intentos y la IP con más intentos es la que tiene 286.
- Importar el mismo log dos veces deja la base con los mismos 520 intentos.
- El panel se genera y se abre sin conexión a internet.
- Hay pruebas automáticas para la importación, las consultas y los casos de log vacío o inexistente.

## Restricciones
- Solo biblioteca estándar de Python (`sqlite3`, `argparse`, `html`).
- Las consultas usan parámetros, nunca texto concatenado, para evitar inyección SQL.
- Los datos de logs de terceros no se suben al repositorio.

## Fuera de alcance (por ahora)
- Ubicación geográfica de las IPs (requiere un servicio externo).
- Análisis en tiempo real y bloqueo de IPs.
