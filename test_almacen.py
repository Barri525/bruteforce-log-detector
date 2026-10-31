import os
import tempfile
import unittest

import almacen


def linea(ip, usuario="root", hora="10"):
    return (
        f"Oct 30 {hora}:15:32 servidor sshd[1]: "
        f"Failed password for {usuario} from {ip} port 22 ssh2\n"
    )


class TestAlmacen(unittest.TestCase):
    def setUp(self):
        # ":memory:" crea una base temporal que desaparece al terminar
        self.conexion = almacen.conectar(":memory:")
        self.addCleanup(self.conexion.close)
        self.carpeta = tempfile.TemporaryDirectory()
        self.addCleanup(self.carpeta.cleanup)

    def crear_log(self, contenido, nombre="prueba.log"):
        ruta = os.path.join(self.carpeta.name, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        return ruta

    def test_extraer_momento(self):
        texto = "Dec  1 06:55:46 LabSZ sshd[1]: algo"
        self.assertEqual(almacen.extraer_momento(texto), "Dec  1 06:55:46")

    def test_extraer_momento_sin_fecha(self):
        self.assertEqual(almacen.extraer_momento("texto sin fecha"), "")

    def test_importa_solo_intentos_fallidos(self):
        contenido = (
            linea("10.0.0.1")
            + linea("10.0.0.2")
            + "Oct 30 10:30:12 servidor sshd[1]: Accepted password "
            "for jorge from 192.0.2.10 port 22 ssh2\n"
            + "Oct 30 10:35:01 servidor CRON[1]: session opened\n"
        )
        lineas, nuevos = almacen.importar(
            self.conexion, self.crear_log(contenido)
        )
        self.assertEqual(lineas, 4)
        self.assertEqual(nuevos, 2)
        self.assertEqual(almacen.totales(self.conexion)["intentos"], 2)

    def test_importar_dos_veces_no_duplica(self):
        ruta = self.crear_log(linea("10.0.0.1") + linea("10.0.0.2"))
        almacen.importar(self.conexion, ruta)
        _, nuevos = almacen.importar(self.conexion, ruta)
        self.assertEqual(nuevos, 0)
        self.assertEqual(almacen.totales(self.conexion)["intentos"], 2)

    def test_top_ips_ordenado(self):
        contenido = linea("10.0.0.1") * 3 + linea("10.0.0.2")
        almacen.importar(self.conexion, self.crear_log(contenido))
        top = almacen.top_ips(self.conexion)
        self.assertEqual(top[0], ("10.0.0.1", 3))
        self.assertEqual(top[1], ("10.0.0.2", 1))

    def test_top_usuarios(self):
        contenido = (
            linea("10.0.0.1", "root") * 2 + linea("10.0.0.1", "admin")
        )
        almacen.importar(self.conexion, self.crear_log(contenido))
        top = almacen.top_usuarios(self.conexion)
        self.assertEqual(top[0], ("root", 2))

    def test_intentos_por_hora(self):
        contenido = (
            linea("10.0.0.1", hora="10") * 2 + linea("10.0.0.1", hora="11")
        )
        almacen.importar(self.conexion, self.crear_log(contenido))
        self.assertEqual(
            almacen.intentos_por_hora(self.conexion),
            [("10", 2), ("11", 1)],
        )

    def test_totales(self):
        contenido = (
            linea("10.0.0.1", "root")
            + linea("10.0.0.2", "root")
            + linea("10.0.0.2", "admin")
        )
        almacen.importar(self.conexion, self.crear_log(contenido))
        self.assertEqual(
            almacen.totales(self.conexion),
            {"intentos": 3, "ips_distintas": 2, "usuarios_distintos": 2},
        )

    def test_archivo_vacio(self):
        lineas, nuevos = almacen.importar(self.conexion, self.crear_log(""))
        self.assertEqual((lineas, nuevos), (0, 0))
        self.assertEqual(almacen.totales(self.conexion)["intentos"], 0)

    def test_archivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            almacen.importar(self.conexion, "no_existe.log")

    def test_texto_malicioso_no_rompe_la_base(self):
        # Un atacante podría poner código SQL como nombre de usuario
        malicioso = "'; DROP TABLE intentos; --"
        contenido = linea("10.0.0.1", malicioso)
        almacen.importar(self.conexion, self.crear_log(contenido))
        self.assertEqual(almacen.totales(self.conexion)["intentos"], 1)
        self.assertEqual(almacen.top_usuarios(self.conexion)[0][0], malicioso)


if __name__ == "__main__":
    unittest.main()