import argparse
import os
import re
import sqlite3

from detector import analizar_linea

# Fecha y hora al inicio de una línea de syslog, por ejemplo "Dec 10 06:55:46"
MOMENTO = re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}")

TABLA = """
CREATE TABLE IF NOT EXISTS intentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    archivo TEXT NOT NULL,
    numero_linea INTEGER NOT NULL,
    momento TEXT NOT NULL,
    ip TEXT NOT NULL,
    usuario TEXT NOT NULL,
    UNIQUE (archivo, numero_linea)
)
"""


def conectar(ruta_db="datos.db"):
    """Abre la base de datos y crea la tabla si todavía no existe."""
    conexion = sqlite3.connect(ruta_db)
    conexion.execute(TABLA)
    conexion.commit()
    return conexion


def extraer_momento(linea):
    """Devuelve la fecha y hora del inicio de la línea, o '' si no la tiene."""
    coincidencia = MOMENTO.match(linea)
    return coincidencia.group(0) if coincidencia else ""


def importar(conexion, ruta_log):
    """Guarda los intentos fallidos del log.
    Devuelve (lineas_leidas, intentos_nuevos)."""
    archivo = os.path.basename(ruta_log)
    lineas_leidas = 0
    antes = conexion.total_changes

    with open(ruta_log, encoding="utf-8", errors="replace") as f:
        for numero, linea in enumerate(f, start=1):
            lineas_leidas += 1
            resultado = analizar_linea(linea)
            if resultado:
                ip, usuario = resultado
                # Los ? son parámetros: los datos nunca se pegan al texto SQL
                conexion.execute(
                    "INSERT OR IGNORE INTO intentos "
                    "(archivo, numero_linea, momento, ip, usuario) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (archivo, numero, extraer_momento(linea), ip, usuario),
                )

    conexion.commit()
    return lineas_leidas, conexion.total_changes - antes


def totales(conexion):
    fila = conexion.execute(
        "SELECT COUNT(*), COUNT(DISTINCT ip), COUNT(DISTINCT usuario) "
        "FROM intentos"
    ).fetchone()
    return {
        "intentos": fila[0],
        "ips_distintas": fila[1],
        "usuarios_distintos": fila[2],
    }


def top_ips(conexion, limite=10):
    return conexion.execute(
        "SELECT ip, COUNT(*) AS n FROM intentos "
        "GROUP BY ip ORDER BY n DESC, ip LIMIT ?",
        (limite,),
    ).fetchall()


def top_usuarios(conexion, limite=10):
    return conexion.execute(
        "SELECT usuario, COUNT(*) AS n FROM intentos "
        "GROUP BY usuario ORDER BY n DESC, usuario LIMIT ?",
        (limite,),
    ).fetchall()


def intentos_por_hora(conexion):
    """Cuenta los intentos por hora del día ('00' a '23')."""
    return conexion.execute(
        "SELECT substr(momento, -8, 2) AS hora, COUNT(*) FROM intentos "
        "WHERE momento != '' GROUP BY hora ORDER BY hora"
    ).fetchall()


def mostrar_resumen(conexion):
    t = totales(conexion)
    if t["intentos"] == 0:
        print("La base de datos está vacía. Importa un log primero.")
        return

    print(f"Intentos fallidos:   {t['intentos']}")
    print(f"IPs distintas:       {t['ips_distintas']}")
    print(f"Usuarios distintos:  {t['usuarios_distintos']}")

    print("\nTop 10 de IPs:")
    for ip, n in top_ips(conexion):
        print(f"  {ip:<16} {n}")

    print("\nTop 10 de usuarios:")
    for usuario, n in top_usuarios(conexion):
        print(f"  {usuario:<12} {n}")

    print("\nIntentos por hora:")
    for hora, n in intentos_por_hora(conexion):
        print(f"  {hora}:00  {n}")


def main():
    parser = argparse.ArgumentParser(
        description="Guarda y consulta intentos fallidos de SSH en SQLite."
    )
    parser.add_argument(
        "--db", default="datos.db", help="Archivo de la base de datos"
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    importar_cmd = subcomandos.add_parser(
        "importar", help="Importa un log a la base de datos"
    )
    importar_cmd.add_argument("archivo", help="Ruta del archivo de log")
    subcomandos.add_parser("resumen", help="Muestra un resumen de los datos")

    args = parser.parse_args()
    conexion = conectar(args.db)

    try:
        if args.comando == "importar":
            try:
                lineas, nuevos = importar(conexion, args.archivo)
            except FileNotFoundError:
                print(f"Error: no se encontró el archivo '{args.archivo}'.")
                return
            if lineas == 0:
                print("El archivo está vacío. No hay nada que importar.")
                return
            print(f"Líneas leídas:             {lineas}")
            print(f"Intentos nuevos guardados: {nuevos}")
        else:
            mostrar_resumen(conexion)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
    