import os
import tempfile
import unittest

import almacen
import panel


def linea(ip, usuario="root", hora="10"):
    return (
        f"Oct 30 {hora}:15:32 servidor sshd[1]: "
        f"Failed password for {usuario} from {ip} port 22 ssh2\n"
    )


class TestOcultarIp(unittest.TestCase):
    def test_oculta_ultimo_numero(self):
        self.assertEqual(panel.ocultar_ip("183.62.140.253"), "183.62.140.xxx")

    def test_texto_que_no_es_ip_no_se_cambia(self):
        self.assertEqual(panel.ocultar_ip("no-es-una-ip"), "no-es-una-ip")


class TestGraficoBarras(unittest.TestCase):
    def test_escapa_html_en_las_etiquetas(self):
        resultado = panel.grafico_barras("Prueba", [("<script>alert(1)</script>", 3)])
        self.assertNotIn("<script>", resultado)
        self.assertIn("&lt;script&gt;", resultado)

    def test_la_barra_mayor_ocupa_el_100_por_ciento(self):
        resultado = panel.grafico_barras("Prueba", [("a", 10), ("b", 5)])
        self.assertIn("width:100.0%", resultado)
        self.assertIn("width:50.0%", resultado)

    def test_sin_datos(self):
        self.assertIn("Sin datos", panel.grafico_barras("Prueba", []))


class TestGenerarHtml(unittest.TestCase):
    def setUp(self):
        self.conexion = almacen.conectar(":memory:")
        self.addCleanup(self.conexion.close)
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)

    def importar(self, contenido):
        ruta = os.path.join(self.carpeta.name, "prueba.log")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        almacen.importar(self.conexion, ruta)

    def test_base_vacia_muestra_aviso(self):
        self.assertIn("No hay datos", panel.generar_html(self.conexion))

    def test_muestra_totales_y_oculta_ips(self):
        self.importar(linea("10.20.30.40") * 3 + linea("10.20.30.41"))
        pagina = panel.generar_html(self.conexion)
        self.assertIn("Intentos fallidos", pagina)
        self.assertIn("10.20.30.xxx", pagina)
        self.assertNotIn("10.20.30.40", pagina)
        self.assertNotIn("10.20.30.41", pagina)

    def test_no_usa_recursos_externos(self):
        self.importar(linea("10.0.0.1"))
        pagina = panel.generar_html(self.conexion)
        self.assertNotIn("http", pagina)
        self.assertNotIn("<script", pagina)

    def test_usuario_malicioso_se_escapa(self):
        self.importar(linea("10.0.0.1", "<img src=x onerror=alert(1)>"))
        pagina = panel.generar_html(self.conexion)
        self.assertNotIn("<img", pagina)

    def test_guardar_panel_crea_el_archivo(self):
        self.importar(linea("10.0.0.1"))
        ruta = os.path.join(self.carpeta.name, "panel.html")
        panel.guardar_panel(self.conexion, ruta)
        self.assertTrue(os.path.exists(ruta))
        with open(ruta, encoding="utf-8") as f:
            self.assertIn("<!DOCTYPE html>", f.read())


if __name__ == "__main__":
    unittest.main()
    