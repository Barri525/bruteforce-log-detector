# Detector de fuerza bruta en logs SSH

Herramienta en Python que analiza logs de autenticación SSH, detecta direcciones IP con muchos intentos fallidos de inicio de sesión (posible ataque de fuerza bruta) y genera un reporte. Proyecto educativo de ciberseguridad.

## ¿Qué problema resuelve?

Un servidor expuesto a internet recibe intentos automáticos de adivinar usuarios y contraseñas. Cada intento queda registrado en el log, pero nadie puede leer miles de líneas a mano. Este programa las analiza y señala qué IPs están atacando.

## Características

- Lee logs de autenticación SSH (formato `sshd` de Linux)
- Cuenta los intentos fallidos por IP y los usuarios más probados
- Marca como sospechosas las IPs que superan un umbral configurable
- Genera un reporte en pantalla y en `reporte.json`
- Sin dependencias externas: solo la biblioteca estándar de Python
- Pruebas automáticas con `unittest`

## Requisitos

- Python 3.8 o superior

## Uso

```bash
python detector.py auth.log
python detector.py auth.log --umbral 10
```

El repositorio incluye `auth.log`, un log de ejemplo para probarlo.

## Ejemplo de resultado

```
Líneas leídas:      17
Intentos fallidos:  14

IPs sospechosas (umbral: 5 intentos):
  198.51.100.23    7 intentos
  203.0.113.5      6 intentos

Usuarios más probados:
  root       6
  admin      3
  test       1
  oracle     1
  ubuntu     1

Reporte guardado en reporte.json
```

## Cómo funciona

1. Lee el archivo línea por línea.
2. Una expresión regular detecta las líneas `Failed password` y extrae la IP y el usuario.
3. `collections.Counter` cuenta los intentos por IP y por usuario.
4. Las IPs con intentos iguales o superiores al umbral se marcan como sospechosas.
5. Se imprime el resumen y se guarda `reporte.json`.

## Pruebas

```bash
python -m unittest -v
```

Las 9 pruebas verifican que el detector:
- extrae bien la IP y el usuario de cada intento fallido,
- ignora logins exitosos y líneas de otro tipo,
- respeta el umbral (5 por defecto, configurable),
- maneja archivos vacíos e inexistentes.

## Metodología

El proyecto se desarrolló siguiendo una especificación escrita antes del código (ver [`SPEC.md`](SPEC.md)) y verificada con pruebas automáticas.

## Limitaciones

- Solo detecta, no bloquea IPs ni modifica el sistema.
- Solo entiende el formato de log de SSH en Linux.
- Un atacante que reparte pocos intentos entre muchas IPs puede quedar por debajo del umbral.
- El umbral por defecto (5) es arbitrario y debe ajustarse a cada caso.

## Próximos pasos

- Probar con logs reales públicos y publicar los resultados
- Gráficos y geolocalización de IPs
- Análisis de ataques capturados en un honeypot propio

## Aviso legal

Proyecto con fines educativos. Los logs de ejemplo usan IPs de rangos reservados para documentación. Úsalo solo con logs propios o de los que tengas autorización.

## Licencia

MIT


## Resultados con datos reales

Probé el detector con una muestra de 2.000 líneas de un servidor OpenSSH real, del conjunto de datos público [Loghub](https://github.com/logpai/loghub).

| Métrica | Resultado |
|---|---|
| Líneas analizadas | 2.000 |
| Intentos fallidos detectados | 520 (26% de la muestra) |
| IPs sospechosas (umbral 5) | 10 |
| Intentos de esas 10 IPs | 496 (95% de los fallos) |
| Usuario más probado | `root`, con 370 intentos (71%) |

Las 5 IPs con más intentos (últimos números ocultos):

| IP | Intentos |
|---|---|
| 183.62.140.xxx | 286 |
| 187.141.143.xxx | 80 |
| 103.99.0.xxx | 46 |
| 112.95.230.xxx | 26 |
| 5.188.10.xxx | 18 |

**Qué muestran los datos:**
- Una sola IP concentra más de la mitad de los intentos, un patrón típico de herramientas automáticas.
- Casi todos los intentos vienen de muy pocas direcciones, por lo que bloquear unas pocas detendría gran parte del ataque.
- Los atacantes prueban primero nombres de usuario comunes como `root`, `admin`, `support` y `oracle`.

**Un caso que encontré con datos reales:** el primer análisis contó 519 intentos en lugar de 520. Una línea tenía un usuario con un espacio extra y mi expresión regular no la reconocía. Corregí la plantilla y agregué una prueba para ese caso.

### Cómo reproducirlo

1. Descarga `OpenSSH_2k.log` desde la carpeta [OpenSSH de Loghub](https://github.com/logpai/loghub/tree/master/OpenSSH).
2. Colócalo en la carpeta del proyecto y ejecuta `python detector.py OpenSSH_2k.log`.

No incluyo el archivo en este repositorio; los datos pertenecen a sus autores.

### Fuente de los datos

Zhu, J., He, S., He, P., Liu, J., Lyu, M. R. *Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics.* IEEE ISSRE, 2023. <https://github.com/logpai/loghub>

