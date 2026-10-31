import argparse
import json
import re
from collections import Counter

# Busca líneas de intento fallido y extrae usuario e IP
PATRON = re.compile(
    r"Failed password for (?:invalid user )?(?P<usuario>\S+) "
    r"from (?P<ip>\d{1,3}(?:\.\d{1,3}){3})"
)


def analizar_linea(linea):
    """Devuelve (ip, usuario) si la línea es un intento fallido; si no, None."""
    coincidencia = PATRON.search(linea)
    if coincidencia is None:
        return None
    return coincidencia.group("ip"), coincidencia.group("usuario")


def analizar_archivo(ruta, umbral=5):
    """Lee el log y devuelve un diccionario con los resultados."""
    intentos_por_ip = Counter()
    usuarios_probados = Counter()
    total_lineas = 0

    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        for linea in archivo:
            total_lineas += 1
            resultado = analizar_linea(linea)
            if resultado:
                ip, usuario = resultado
                intentos_por_ip[ip] += 1
                usuarios_probados[usuario] += 1

    sospechosas = {
        ip: n for ip, n in intentos_por_ip.most_common() if n >= umbral
    }

    return {
        "lineas_leidas": total_lineas,
        "intentos_fallidos": sum(intentos_por_ip.values()),
        "umbral": umbral,
        "ips_sospechosas": sospechosas,
        "usuarios_mas_probados": dict(usuarios_probados.most_common(5)),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Detecta posibles ataques de fuerza bruta en un log SSH."
    )
    parser.add_argument("archivo", help="Ruta del archivo de log")
    parser.add_argument(
        "--umbral",
        type=int,
        default=5,
        help="Intentos fallidos para considerar una IP sospechosa (por defecto 5)",
    )
    args = parser.parse_args()

    try:
        reporte = analizar_archivo(args.archivo, args.umbral)
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{args.archivo}'.")
        return

    if reporte["lineas_leidas"] == 0:
        print("El archivo está vacío. No hay nada que analizar.")
        return

    print(f"Líneas leídas:      {reporte['lineas_leidas']}")
    print(f"Intentos fallidos:  {reporte['intentos_fallidos']}")
    print(f"\nIPs sospechosas (umbral: {args.umbral} intentos):")
    if reporte["ips_sospechosas"]:
        for ip, n in reporte["ips_sospechosas"].items():
            print(f"  {ip:<16} {n} intentos")
    else:
        print("  Ninguna.")

    print("\nUsuarios más probados:")
    for usuario, n in reporte["usuarios_mas_probados"].items():
        print(f"  {usuario:<10} {n}")

    with open("reporte.json", "w", encoding="utf-8") as salida:
        json.dump(reporte, salida, indent=2, ensure_ascii=False)
    print("\nReporte guardado en reporte.json")


if __name__ == "__main__":
    main()

    