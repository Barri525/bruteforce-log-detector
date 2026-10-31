import os
import tempfile
import unittest

from detector import analizar_archivo, analizar_linea

LINEA_FALLIDA = (
    "Oct 30 10:00:00 servidor sshd[1]: "
    "Failed password for root from {ip} port 22 ssh2\n"
)


class TestAnalizarLinea(unittest.TestCase):
    def test_fallo_con_usuario_invalido(self):
        linea = (
            "Oct 30 10:15:32 servidor sshd[1234]: Failed password "
            "for invalid user admin from 203.0.113.5 port 52144 ssh2"
        )
        self.assertEqual(analizar_linea(linea), ("203.0.113.5", "admin"))

    def test_fallo_con_usuario_valido(self):
        linea = (
            "Oct 30 10:20:10 servidor sshd[1301]: Failed password "
            "for root from 198.51.100.23 port 40010 ssh2"
        )
        self.assertEqual(analizar_linea(linea), ("198.51.100.23", "root"))

    def test_login_exitoso_se_ignora(self):
        linea = (
            "Oct 30 10:30:12 servidor sshd[1450]: Accepted password "
            "for jorge from 192.0.2.10 port 51200 ssh2"
        )
        self.assertIsNone(analizar_linea(linea))

    def test_linea_de_otro_tipo_se_ignora(self):
        linea = (
            "Oct 30 10:35:01 servidor CRON[1600]: "
            "pam_unix(cron:session): session opened for user root"
        )
        self.assertIsNone(analizar_linea(linea))


class TestAnalizarArchivo(unittest.TestCase):
    def crear_log(self, contenido):
        carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(carpeta.cleanup)
        ruta = os.path.join(carpeta.name, "prueba.log")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta

    def test_ip_con_cinco_fallos_es_sospechosa(self):
        ruta = self.crear_log(LINEA_FALLIDA.format(ip="10.0.0.1") * 5)
        reporte = analizar_archivo(ruta)
        self.assertIn("10.0.0.1", reporte["ips_sospechosas"])

    def test_ip_con_cuatro_fallos_no_es_sospechosa(self):
        ruta = self.crear_log(LINEA_FALLIDA.format(ip="10.0.0.1") * 4)
        reporte = analizar_archivo(ruta)
        self.assertEqual(reporte["ips_sospechosas"], {})

    def test_umbral_configurable(self):
        ruta = self.crear_log(LINEA_FALLIDA.format(ip="10.0.0.1") * 3)
        reporte = analizar_archivo(ruta, umbral=3)
        self.assertIn("10.0.0.1", reporte["ips_sospechosas"])

    def test_archivo_vacio(self):
        ruta = self.crear_log("")
        reporte = analizar_archivo(ruta)
        self.assertEqual(reporte["lineas_leidas"], 0)

    def test_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            analizar_archivo("no_existe.log")


if __name__ == "__main__":
    unittest.main()

    