import argparse
import html

import almacen

ESTILO = """
:root { color-scheme: light dark; --fondo: #f6f7f9; --tarjeta: #ffffff;
  --texto: #1c1f24; --suave: #5b6470; --borde: #dfe3e8; --barra: #3b82f6; }
@media (prefers-color-scheme: dark) {
  :root { --fondo: #0f1318; --tarjeta: #181d24; --texto: #e8ebef;
    --suave: #9aa4b1; --borde: #2a313b; --barra: #5b9dff; }
}
* { box-sizing: border-box; }
body { margin: 0; padding: 24px; background: var(--fondo); color: var(--texto);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 960px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 4px; }
.sub { color: var(--suave); margin: 0 0 24px; }
.tarjetas { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px; margin-bottom: 16px; }
.tarjeta, section { background: var(--tarjeta); border: 1px solid var(--borde);
  border-radius: 10px; padding: 16px; }
.tarjeta .num { font-size: 1.8rem; font-weight: 600; }
.tarjeta .rotulo { color: var(--suave); font-size: .9rem; }
section { margin-bottom: 16px; }
h2 { font-size: 1.05rem; margin: 0 0 12px; }
.fila { display: grid; grid-template-columns: 130px 1fr 56px; gap: 10px;
  align-items: center; margin: 6px 0; font-size: .9rem; }
.etiqueta { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.barra { background: var(--borde); border-radius: 4px; height: 14px; overflow: hidden; }
.relleno { background: var(--barra); height: 100%; }
.valor { text-align: right; font-variant-numeric: tabular-nums; }
.vacio, .nota { color: var(--suave); }
.nota { font-size: .85rem; margin-top: 24px; }
"""


def ocultar_ip(ip):
    """Oculta el último número de una IPv4: 183.62.140.253 -> 183.62.140.xxx"""
    partes = ip.split(".")
    if len(partes) == 4:
        return ".".join(partes[:3] + ["xxx"])
    return ip


def grafico_barras(titulo, datos):
    """Devuelve el HTML de un gráfico de barras. datos: lista de (etiqueta, valor)."""
    encabezado = f"<h2>{html.escape(titulo)}</h2>"
    if not datos:
        return f"<section>{encabezado}<p class='vacio'>Sin datos.</p></section>"

    maximo = max(valor for _, valor in datos)
    filas = []
    for etiqueta, valor in datos:
        ancho = round(valor / maximo * 100, 1)
        filas.append(
            "<div class='fila'>"
            f"<span class='etiqueta'>{html.escape(str(etiqueta))}</span>"
            f"<div class='barra'><div class='relleno' style='width:{ancho}%'></div></div>"
            f"<span class='valor'>{valor}</span>"
            "</div>"
        )
    return f"<section>{encabezado}{''.join(filas)}</section>"


def tarjeta(numero, rotulo):
    return (
        "<div class='tarjeta'>"
        f"<div class='num'>{numero}</div>"
        f"<div class='rotulo'>{html.escape(rotulo)}</div>"
        "</div>"
    )


def generar_html(conexion):
    """Construye la página completa a partir de la base de datos."""
    t = almacen.totales(conexion)

    if t["intentos"] == 0:
        cuerpo = "<section><p class='vacio'>No hay datos. Importa un log primero.</p></section>"
    else:
        ips = [(ocultar_ip(ip), n) for ip, n in almacen.top_ips(conexion)]
        usuarios = almacen.top_usuarios(conexion)
        horas = [(f"{h}:00", n) for h, n in almacen.intentos_por_hora(conexion)]
        cuerpo = (
            "<div class='tarjetas'>"
            + tarjeta(t["intentos"], "Intentos fallidos")
            + tarjeta(t["ips_distintas"], "IPs distintas")
            + tarjeta(t["usuarios_distintos"], "Usuarios distintos")
            + "</div>"
            + grafico_barras("Top 10 de IPs (último número oculto)", ips)
            + grafico_barras("Top 10 de usuarios más probados", usuarios)
            + grafico_barras("Intentos por hora del día", horas)
            + "<p class='nota'>Panel generado a partir de los intentos fallidos de SSH "
            "guardados en la base de datos. Si el log cubre pocas horas, "
            "la distribución por hora no representa un día completo.</p>"
        )

    return (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>Panel de intentos de fuerza bruta</title>"
        f"<style>{ESTILO}</style></head><body><main>"
        "<h1>Panel de intentos de fuerza bruta</h1>"
        "<p class='sub'>Intentos fallidos de inicio de sesión SSH</p>"
        f"{cuerpo}</main></body></html>"
    )


def guardar_panel(conexion, ruta_salida="panel.html"):
    contenido = generar_html(conexion)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta_salida


def main():
    parser = argparse.ArgumentParser(
        description="Genera un panel HTML con gráficos a partir de la base de datos."
    )
    parser.add_argument("--db", default="datos.db", help="Archivo de la base de datos")
    parser.add_argument("--salida", default="panel.html", help="Archivo HTML de salida")
    args = parser.parse_args()

    conexion = almacen.conectar(args.db)
    try:
        ruta = guardar_panel(conexion, args.salida)
    finally:
        conexion.close()
    print(f"Panel generado: {ruta}")


if __name__ == "__main__":
    main()