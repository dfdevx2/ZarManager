"""Testes do leitor GOD/SVOD.

Ver o aviso em god_builder.py sobre o alcance destes testes.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.xbox import god                                        # noqa: E402
from core.xbox.god import GodCancelled, GodError, GodPackage, Layout, SECTOR, is_god  # noqa: E402
from tests.god_builder import GodBuilder, make_xdvdfs_image      # noqa: E402

# Um ficheiro de dados real leva 0xA290000 bytes. Para exercitar a travessia
# entre data0000 e data0001 sem escrever 170 MB, encolhe-se a geometria: a
# aritmética testada é a mesma, só as constantes é que são menores.
SMALL_FILE_SECTORS = 0x330          # 2 grupos por ficheiro


class GodReaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="god-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def roundtrip(self, layout: Layout, sectors: int = 100, **kwargs) -> tuple[bytes, bytes]:
        image = make_xdvdfs_image(sectors)
        header = GodBuilder(layout, **kwargs).build(self.tmp / "8A1B2C3D", image)

        saida = self.tmp / "saida.iso"
        with GodPackage(header) as package:
            package.rebuild(saida)
        return image, saida.read_bytes()

    # --------------------------------------------------------- reconstrução
    def test_reconstroi_imagem_byte_a_byte(self):
        original, reconstruida = self.roundtrip(Layout(base=0x2000, lead_sectors=0))
        self.assertEqual(reconstruida[:len(original)], original)

    def test_salta_as_tabelas_de_hash(self):
        """Mais de 0x198 sectores: obriga a contar as tabelas intercaladas.

        É aqui que um erro de geometria aparece -- abaixo de um grupo, tudo
        passa mesmo com a fórmula errada.
        """
        original, reconstruida = self.roundtrip(
            Layout(base=0x2000, lead_sectors=0), sectors=god.SECTORS_PER_GROUP + 50
        )
        self.assertEqual(reconstruida[:len(original)], original)

    def test_atravessa_varios_ficheiros_de_dados(self):
        with mock.patch.object(god, "SECTORS_PER_FILE", SMALL_FILE_SECTORS):
            original, reconstruida = self.roundtrip(
                Layout(base=0x2000, lead_sectors=0), sectors=SMALL_FILE_SECTORS * 2 + 30
            )
        self.assertEqual(reconstruida[:len(original)], original)

        dados = self.tmp / "8A1B2C3D.data"
        self.assertTrue((dados / "data0002").exists(), "devia ter partido em três")

    # --------------------------------------------------------------- probe
    def test_encontra_a_geometria_sozinho(self):
        """Cada variante possível tem de ser reconhecida pelo que ela é."""
        variantes = [
            (Layout(base=0x2000, lead_sectors=0), True),
            (Layout(base=0x12000, lead_sectors=0), True),
            (Layout(base=0x2000, lead_sectors=32), True),
            (Layout(base=0x12000, lead_sectors=32), False),    # offset em little endian
        ]
        for layout, big_endian in variantes:
            with self.subTest(base=hex(layout.base), lead=layout.lead_sectors):
                destino = self.tmp / f"pkg{layout.base}{layout.lead_sectors}{big_endian}"
                image = make_xdvdfs_image(god.SECTORS_PER_GROUP + 20)
                header = GodBuilder(layout, offset_big_endian=big_endian).build(destino, image)

                with GodPackage(header) as package:
                    self.assertEqual(package.layout, layout)
                    saida = self.tmp / f"{destino.name}.iso"
                    package.rebuild(saida)

                reconstruida = saida.read_bytes()
                inicio = layout.lead_sectors * SECTOR
                # Os sectores anteriores ao fluxo não estão guardados em lado
                # nenhum: saem a zeros, que é o que lá está num XGD real.
                self.assertEqual(reconstruida[:inicio], b"\x00" * inicio)
                self.assertEqual(reconstruida[inicio:len(image)], image[inicio:])

    def test_recusa_geometria_irreconhecivel(self):
        """Sem a assinatura no sítio, escrever uma imagem seria pior que falhar."""
        image = bytearray(make_xdvdfs_image(60))
        image[0x10000:0x10000 + 20] = b"\x00" * 20          # apaga a assinatura
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.tmp / "partido", bytes(image)
        )

        with self.assertRaises(GodError):
            with GodPackage(header):
                pass

    def test_recusa_pasta_de_dados_ausente(self):
        image = make_xdvdfs_image(60)
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.tmp / "semdados", image
        )
        shutil.rmtree(self.tmp / "semdados.data")

        self.assertFalse(is_god(header))
        with self.assertRaises(GodError):
            with GodPackage(header):
                pass

    def test_recusa_peca_em_falta(self):
        """Um data0001 apagado dava uma imagem corrompida em silêncio."""
        with mock.patch.object(god, "SECTORS_PER_FILE", SMALL_FILE_SECTORS):
            image = make_xdvdfs_image(SMALL_FILE_SECTORS * 2 + 10)
            header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
                self.tmp / "incompleto", image
            )
            (self.tmp / "incompleto.data" / "data0001").unlink()

            with self.assertRaises(GodError) as caso:
                with GodPackage(header):
                    pass
        self.assertIn("data0001", str(caso.exception))

    # -------------------------------------------------------- comportamento
    def test_deteta_god(self):
        image = make_xdvdfs_image(60)
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.tmp / "C0DEF10E", image
        )
        self.assertTrue(is_god(header))

        solto = self.tmp / "qualquer.bin"
        solto.write_bytes(b"nao e god" * 10)
        self.assertFalse(is_god(solto))

    def test_progresso_e_monotono_e_chega_a_um(self):
        image = make_xdvdfs_image(god.SECTORS_PER_GROUP + 20)
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.tmp / "progresso", image
        )

        valores = []
        with GodPackage(header) as package:
            package.rebuild(
                self.tmp / "p.iso",
                progress=lambda ratio, _name: valores.append(ratio),
                chunk_sectors=64,
            )

        self.assertTrue(valores)
        self.assertEqual(valores, sorted(valores), "o progresso recuou")
        self.assertAlmostEqual(valores[-1], 1.0, places=6)

    def test_cancelamento_interrompe(self):
        image = make_xdvdfs_image(god.SECTORS_PER_GROUP + 20)
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.tmp / "cancelar", image
        )

        with GodPackage(header) as package:
            with self.assertRaises(GodCancelled):
                package.rebuild(self.tmp / "c.iso", should_cancel=lambda: True)

    def test_describe_devolve_metadados(self):
        image = make_xdvdfs_image(60)
        header = GodBuilder(
            Layout(base=0x2000, lead_sectors=0),
            title_id=0x4D5307D5,
            display_name="Jogo GOD",
        ).build(self.tmp / "meta", image)

        info = god.describe(header)
        self.assertEqual(info["title_id"], "4D5307D5")
        self.assertEqual(info["name"], "Jogo GOD")
        self.assertEqual(info["parts"], 1)
        self.assertEqual(info["base"], "0x2000")


if __name__ == "__main__":
    unittest.main(verbosity=2)
