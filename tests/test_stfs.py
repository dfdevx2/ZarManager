"""Testes do leitor STFS.

Ver o aviso em stfs_builder.py sobre o alcance destes testes: validam a
coerência do leitor, não a compatibilidade com pacotes de retalho.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.xbox.stfs import BLOCK_SIZE, StfsError, StfsPackage, describe, is_stfs  # noqa: E402
from tests.stfs_builder import ENTRIES_PER_TABLE, StfsBuilder  # noqa: E402


class StfsReaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="stfs-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build(self, files, **kwargs) -> Path:
        builder = StfsBuilder(**kwargs)
        for path, data, *rest in files:
            builder.add_file(path, data, contiguous=rest[0] if rest else True)
        return builder.build(self.tmp / "pacote")

    def extract(self, package_path: Path) -> Path:
        destination = self.tmp / "saida"
        with StfsPackage(package_path) as package:
            package.extract_all(destination)
        return destination

    # ------------------------------------------------------------- básico
    def test_deteta_magic(self):
        package = self.build([("default.xex", b"XEX2" + b"\x00" * 100)])
        self.assertTrue(is_stfs(package))

        outro = self.tmp / "qualquer.bin"
        outro.write_bytes(b"nao e stfs" * 10)
        self.assertFalse(is_stfs(outro))

    def test_recusa_ficheiro_que_nao_e_stfs(self):
        outro = self.tmp / "qualquer.bin"
        outro.write_bytes(b"\x00" * 0x2000)
        with self.assertRaises(StfsError):
            with StfsPackage(outro):
                pass

    def test_extrai_ficheiros_da_raiz(self):
        conteudos = {
            "default.xex": b"XEX2" + os.urandom(5000),
            "leia.txt": b"ola mundo",
            "icone.png": os.urandom(BLOCK_SIZE * 3),
        }
        package = self.build([(nome, dados) for nome, dados in conteudos.items()])
        destino = self.extract(package)

        for nome, dados in conteudos.items():
            with self.subTest(ficheiro=nome):
                self.assertEqual((destino / nome).read_bytes(), dados)

    def test_preserva_subdiretorios(self):
        package = self.build([
            ("default.xex", b"XEX2raiz"),
            ("media/audio/musica.bin", os.urandom(3000)),
            ("media/textura.bin", os.urandom(9000)),
        ])
        destino = self.extract(package)

        self.assertTrue((destino / "default.xex").exists())
        self.assertTrue((destino / "media" / "textura.bin").exists())
        self.assertTrue((destino / "media" / "audio" / "musica.bin").exists())

    def test_ficheiro_nao_contiguo_segue_a_cadeia(self):
        """Blocos fora de ordem: só a cadeia das tabelas de hash os liga."""
        dados = os.urandom(BLOCK_SIZE * 5 + 123)
        package = self.build([("fragmentado.bin", dados, False)])
        destino = self.extract(package)

        self.assertEqual((destino / "fragmentado.bin").read_bytes(), dados)

    def test_pacote_atravessa_a_fronteira_das_tabelas(self):
        """Mais de 0xAA blocos: obriga a contar as tabelas intercaladas.

        É aqui que um erro de endereçamento aparece -- tudo abaixo de 0xAA
        blocos passa mesmo com a fórmula errada.
        """
        grande = os.urandom(BLOCK_SIZE * (ENTRIES_PER_TABLE + 40))
        pequeno = b"depois da fronteira"
        package = self.build([("grande.bin", grande), ("pequeno.txt", pequeno)])
        destino = self.extract(package)

        self.assertEqual((destino / "grande.bin").read_bytes(), grande)
        self.assertEqual((destino / "pequeno.txt").read_bytes(), pequeno)

    def test_tabela_de_ficheiros_com_varios_blocos(self):
        """Mais de 64 entradas: a própria tabela passa a ocupar vários blocos."""
        ficheiros = [(f"ficheiro_{i:03d}.bin", f"conteudo {i}".encode()) for i in range(150)]
        package = self.build(ficheiros)
        destino = self.extract(package)

        for nome, dados in ficheiros:
            with self.subTest(ficheiro=nome):
                self.assertEqual((destino / nome).read_bytes(), dados)

    # ----------------------------------------------------------- segurança
    def test_nome_com_travessia_fica_dentro_do_destino(self):
        package = self.build([("..%2f..%2fevil.txt", b"nao devia sair")])
        destino = self.extract(package)

        escritos = list(destino.rglob("*"))
        for caminho in escritos:
            self.assertTrue(
                destino.resolve() in caminho.resolve().parents or caminho.resolve() == destino.resolve(),
                f"{caminho} saiu do destino",
            )

    # -------------------------------------------------------- comportamento
    def test_progresso_e_monotono_e_chega_a_um(self):
        package = self.build([
            ("a.bin", os.urandom(BLOCK_SIZE * 4)),
            ("b.bin", os.urandom(BLOCK_SIZE * 6)),
        ])
        valores = []
        with StfsPackage(package) as pkg:
            pkg.extract_all(self.tmp / "p", progress=lambda ratio, _name: valores.append(ratio))

        self.assertTrue(valores)
        self.assertEqual(valores, sorted(valores), "o progresso recuou")
        self.assertAlmostEqual(valores[-1], 1.0, places=6)

    def test_cancelamento_interrompe(self):
        package = self.build([(f"f{i}.bin", os.urandom(BLOCK_SIZE)) for i in range(20)])
        with StfsPackage(package) as pkg:
            with self.assertRaises(StfsError):
                pkg.extract_all(self.tmp / "c", should_cancel=lambda: True)

    def test_describe_devolve_metadados(self):
        package = self.build(
            [("default.xex", b"XEX2")],
            title_id=0x4D5307D5,
            display_name="Jogo Exemplo",
        )
        info = describe(package)
        self.assertEqual(info["title_id"], "4D5307D5")
        self.assertEqual(info["name"], "Jogo Exemplo")
        self.assertEqual(info["files"], 1)
        self.assertEqual(info["magic"], "CON")


if __name__ == "__main__":
    unittest.main(verbosity=2)
