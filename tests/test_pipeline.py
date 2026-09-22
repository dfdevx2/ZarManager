"""Testes ponta a ponta do core, com motores falsos.

Cobrem exactamente os bugs corrigidos na Fase 0: integridade do resultado,
transação dos originais, colisões, cancelamento e propagação do motor ausente.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.engines import EngineResolver          # noqa: E402
from core.errors import EngineMissing            # noqa: E402
from core.events import ItemState                # noqa: E402
from core.job import JobRequest, JobRunner       # noqa: E402
from core.planner import Mode                    # noqa: E402
from core.workspace import WORK_DIR_NAME         # noqa: E402

FAKE_BIN = ROOT / "tests" / "fake_bin"


def make_xbox_iso(path: Path) -> Path:
    data = bytearray(0x20000)
    data[0x10000:0x10000 + 20] = b"MICROSOFT*XBOX*MEDIA"
    path.write_bytes(bytes(data))
    return path


def make_zip_with_game(path: Path) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Jogo/default.xex", "XEX2fake")
        zf.writestr("Jogo/media/asset.bin", "\0" * 32)
    return path


def make_game_dir(path: Path) -> Path:
    (path / "media").mkdir(parents=True, exist_ok=True)
    (path / "default.xex").write_bytes(b"XEX2fake")
    (path / "media" / "asset.bin").write_bytes(b"\0" * 32)
    return path


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="zar-test-"))
        self.source = self.tmp / "origem"
        self.target = self.tmp / "destino"
        self.source.mkdir()
        self.target.mkdir()
        self.events = []
        self.items = []
        for key in ("ZAR_FAKE_FAIL", "ZAR_FAKE_RC1", "ZAR_FAKE_SLOW"):
            os.environ.pop(key, None)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        for key in ("ZAR_FAKE_FAIL", "ZAR_FAKE_RC1", "ZAR_FAKE_SLOW"):
            os.environ.pop(key, None)

    def build(self, items, mode=Mode.AUTO, **kwargs):
        request = JobRequest(
            items=[Path(i) for i in items],
            target=self.target,
            mode=mode,
            workers=kwargs.pop("workers", 2),
            **kwargs,
        )
        return JobRunner(
            request,
            on_event=self.events.append,
            on_item=self.items.append,
            resolver=EngineResolver(FAKE_BIN),
        )

    def final_states(self):
        return {s.name: s.state for s in self.items if s.state.is_final}

    def leftovers(self):
        return list((self.target / WORK_DIR_NAME).glob("*")) if (self.target / WORK_DIR_NAME).exists() else []

    # ------------------------------------------------------------ cadeias
    def test_auto_zip_para_zar(self):
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item]).run()

        self.assertEqual(result.completed, 1)
        self.assertEqual(result.failed, 0)
        self.assertTrue((self.target / "Jogo.zar").exists())
        self.assertFalse(item.exists(), "o original devia ter sido apagado")
        self.assertEqual(self.leftovers(), [], "sobraram ficheiros de trabalho")

    def test_auto_iso_xbox_para_zar(self):
        item = make_xbox_iso(self.source / "Halo.iso")
        result = self.build([item]).run()

        self.assertEqual(result.completed, 1)
        self.assertTrue((self.target / "Halo.zar").exists())

    def test_modo_extrair_arquivo_para_no_diretorio(self):
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item], mode=Mode.EXTRACT_ARC).run()

        self.assertEqual(result.completed, 1)
        destino = self.target / "Jogo"
        self.assertTrue(destino.is_dir())
        self.assertTrue((destino / "default.xex").exists(),
                        "'7z x' tem de preservar a estrutura de pastas")
        self.assertFalse((self.target / "Jogo.zar").exists())

    def test_modo_comprimir_pasta(self):
        item = make_game_dir(self.source / "Forza")
        result = self.build([item], mode=Mode.COMPRESS).run()

        self.assertEqual(result.completed, 1)
        self.assertTrue((self.target / "Forza.zar").exists())
        self.assertFalse(item.exists())

    def test_manter_originais(self):
        item = make_zip_with_game(self.source / "Jogo.zip")
        self.build([item], keep_originals=True).run()

        self.assertTrue(item.exists(), "o original devia ter sido mantido")
        self.assertTrue((self.target / "Jogo.zar").exists())

    # ---------------------------------------------------------- robustez
    def test_codigo_1_do_7zip_e_tolerado(self):
        os.environ["ZAR_FAKE_RC1"] = "1"
        item = make_zip_with_game(self.source / "Scene.zip")
        result = self.build([item]).run()

        self.assertEqual(result.completed, 1, "rc=1 do 7z tem de ser um aviso, não uma falha")

    def test_falha_tardia_preserva_o_original(self):
        """O bug antigo: o zip era apagado logo após a extração; se o zarchive
        falhasse a seguir, o utilizador ficava sem original e sem resultado."""
        os.environ["ZAR_FAKE_FAIL"] = "zar"
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item]).run()

        self.assertEqual(result.failed, 1)
        self.assertEqual(result.completed, 0)
        self.assertTrue(item.exists(), "o original TEM de sobreviver a uma falha tardia")
        self.assertFalse((self.target / "Jogo.zar").exists())
        self.assertEqual(self.leftovers(), [])
        self.assertEqual(self.final_states()["Jogo.zip"], ItemState.FAILED)

    def test_resultado_parcial_e_reportado(self):
        bom = make_game_dir(self.source / "Bom")
        mau = self.source / "Corrompido.iso"
        mau.write_bytes(b"lixo" * 10)              # não é reconhecido

        result = self.build([bom, mau]).run()
        self.assertEqual(result.completed, 1)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.state_key, "completed")

    def test_verify_environment_nomeia_o_motor_em_falta(self):
        """Antes devolvia só um bool e a UI mostrava sempre
        'Ficheiros desconhecidos' em vez do nome do motor."""
        vazio = self.tmp / "sem-motores"
        vazio.mkdir()
        item = make_game_dir(self.source / "Forza")

        request = JobRequest(items=[item], target=self.target, mode=Mode.COMPRESS)
        runner = JobRunner(request, resolver=EngineResolver(vazio))

        ok, missing = runner.verify_environment()
        self.assertFalse(ok)
        self.assertIn("ZArchive", missing)

    def test_motor_apagado_a_meio_sobe_ate_ao_chamador(self):
        """O cenário real do antivírus: o motor existe no arranque e
        desaparece a meio. Antes, o AV_BLOCK era engolido por um
        `except Exception` dentro do start_processing e o alerta na UI
        era código morto."""
        os.environ["ZAR_FAKE_SLOW"] = "2"
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        for engine in FAKE_BIN.iterdir():
            shutil.copy2(engine, bin_dir / engine.name)

        item = make_zip_with_game(self.source / "Jogo.zip")
        request = JobRequest(items=[item], target=self.target, mode=Mode.AUTO, workers=1)
        runner = JobRunner(request, on_event=self.events.append,
                           on_item=self.items.append,
                           resolver=EngineResolver(bin_dir))

        ok, _ = runner.verify_environment()
        self.assertTrue(ok, "no arranque o ambiente está completo")

        # o "antivírus" apaga o zarchive enquanto o 7z ainda corre
        threading.Timer(0.8, lambda: (bin_dir / "zarchive").unlink()).start()

        with self.assertRaises(EngineMissing) as ctx:
            runner.run()

        self.assertEqual(ctx.exception.engine_id, "zar")
        self.assertTrue(item.exists(), "um motor em falta não pode custar o original")
        self.assertEqual(self.leftovers(), [])

    # ---------------------------------------------------------- colisões
    def test_colisao_skip(self):
        (self.target / "Jogo.zar").write_text("antigo")
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item], policy="SKIP").run()

        self.assertEqual(result.skipped, 1)
        self.assertEqual((self.target / "Jogo.zar").read_text(), "antigo")
        self.assertTrue(item.exists(), "um item ignorado não pode perder o original")

    def test_colisao_rename(self):
        (self.target / "Jogo.zar").write_text("antigo")
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item], policy="RENAME").run()

        self.assertEqual(result.completed, 1)
        self.assertTrue((self.target / "Jogo_1.zar").exists())
        self.assertEqual((self.target / "Jogo.zar").read_text(), "antigo")

    def test_colisao_overwrite(self):
        (self.target / "Jogo.zar").write_text("antigo")
        item = make_zip_with_game(self.source / "Jogo.zip")
        result = self.build([item], policy="OVERWRITE").run()

        self.assertEqual(result.completed, 1)
        self.assertNotEqual((self.target / "Jogo.zar").read_text(), "antigo")

    def test_lote_paralelo_sem_colisao_de_nomes(self):
        items = [make_zip_with_game(self.source / f"Jogo{i}.zip") for i in range(6)]
        result = self.build(items, workers=4).run()

        self.assertEqual(result.completed, 6)
        self.assertEqual(len(list(self.target.glob("*.zar"))), 6)
        self.assertEqual(self.leftovers(), [])

    # ------------------------------------------------------ cancelamento
    def test_cancelamento_nao_deixa_lixo(self):
        os.environ["ZAR_FAKE_SLOW"] = "2"
        items = [make_zip_with_game(self.source / f"Jogo{i}.zip") for i in range(3)]
        runner = self.build(items, workers=1)

        threading.Timer(0.6, runner.cancel).start()
        started = time.monotonic()
        result = runner.run()
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 8, "o cancelamento tem de interromper o motor, não esperar por ele")
        self.assertTrue(runner.is_cancelled)
        self.assertEqual(result.state_key, "cancelled")
        self.assertEqual(result.completed + result.failed + result.cancelled + result.skipped, 3)
        self.assertEqual(self.leftovers(), [])
        self.assertEqual(list(self.target.glob("*.zar")), [],
                         "nada pode chegar ao destino num lote cancelado")
        for item in items:
            self.assertTrue(item.exists(), "cancelar não pode apagar originais")

    def test_pausa_e_retoma(self):
        os.environ["ZAR_FAKE_SLOW"] = "1"
        items = [make_zip_with_game(self.source / f"Jogo{i}.zip") for i in range(2)]
        runner = self.build(items, workers=1)

        def pausar():
            self.assertTrue(runner.toggle_pause())
            time.sleep(0.8)
            self.assertFalse(runner.toggle_pause())

        threading.Timer(0.4, pausar).start()
        result = runner.run()
        self.assertEqual(result.completed, 2)




class RobustnessTest(PipelineTest):
    # Herda o setUp/tearDown; os testes herdados correm outra vez, o que é
    # barato e serve de rede de segurança.
    def test_motor_que_nao_escreve_nada_e_falha(self):
        """Um motor pode devolver 0 sem produzir saída (disco cheio, arquivo
        vazio). Antes seguia-se para a etapa seguinte com uma pasta vazia."""
        vazio = self.source / "Vazio.zip"
        with zipfile.ZipFile(vazio, "w"):
            pass

        result = self.build([vazio]).run()
        self.assertEqual(result.completed, 0)
        self.assertEqual(result.failed, 1)
        self.assertTrue(vazio.exists(), "o original tem de sobreviver")
        self.assertEqual(list(self.target.glob("*.zar")), [])

    def test_faixas_bin_nao_aparecem_soltas(self):
        """Uma imagem de CD é um .cue com .bin ao lado; listar as faixas
        soltas punha-as na fila como se fossem jogos."""
        from services.file_service import FileService

        (self.source / "Jogo.cue").write_text('FILE "Jogo.bin" BINARY')
        (self.source / "Jogo.bin").write_bytes(b"\0" * 64)

        nomes = sorted(p.name for p in
                       FileService.find_processable_files(str(self.source), Mode.AUTO))
        self.assertIn("Jogo.cue", nomes)
        self.assertNotIn("Jogo.bin", nomes)

    # ------------------------------------------------- contentores Xbox 360
    def test_auto_pacote_stfs_para_zar(self):
        """Etapa nativa dentro do pipeline: sem binário, mesma cadeia."""
        from tests.stfs_builder import StfsBuilder

        pacote = self.source / "Trials HD"
        StfsBuilder(display_name="Trials HD").add_file(
            "default.xex", b"XEX2" + b"\0" * 2000
        ).add_file("media/som.bin", b"\1" * 5000).build(pacote)

        result = self.build([pacote]).run()

        self.assertEqual(result.failed, 0)
        self.assertEqual(result.completed, 1)
        self.assertTrue((self.target / "Trials HD.zar").exists())
        self.assertFalse(pacote.exists(), "o original devia ter sido apagado")
        self.assertEqual(self.leftovers(), [])

    def test_modo_extrair_pacote_stfs(self):
        from tests.stfs_builder import StfsBuilder

        pacote = self.source / "DLC"
        StfsBuilder().add_file("conteudo/mapa.bin", b"mapa" * 500).build(pacote)

        result = self.build([pacote], mode=Mode.EXTRACT_ISO).run()

        self.assertEqual(result.completed, 1)
        destino = self.target / "DLC"
        self.assertTrue((destino / "conteudo" / "mapa.bin").exists())

    def test_stfs_nao_precisa_de_motor_externo(self):
        """Com bin/ vazio, o STFS continua disponível e o XISO não."""
        from core.planner import Planner
        from core.formats import Fmt

        vazio = EngineResolver(self.tmp / "sem-motores")
        planner = Planner(vazio, Mode.AUTO)

        self.assertIn("stfs", planner.available_ids)
        self.assertNotIn("xiso", planner.available_ids)
        self.assertEqual(planner.route(Fmt.STFS, Fmt.GAME_DIR)[0].id, "stfs")

    def test_deteta_stfs_dentro_de_pasta(self):
        """Um XBLA sai de um .zip como um ficheiro sem extensão, sozinho."""
        from core.formats import Fmt, payload_path, sniff
        from tests.stfs_builder import StfsBuilder

        pasta = self.source / "extraido"
        pasta.mkdir()
        pacote = pasta / "C0DEF10E"
        StfsBuilder().add_file("default.xex", b"XEX2").build(pacote)

        self.assertIs(sniff(pacote), Fmt.STFS)
        self.assertIs(sniff(pasta), Fmt.STFS)
        self.assertEqual(payload_path(pasta), pacote)

    def test_distingue_god_de_pacote_stfs(self):
        """Mesmo cabeçalho; o que muda é a pasta .data ao lado."""
        from core.formats import Fmt, payload_path, sniff
        from tests.stfs_builder import StfsBuilder

        pasta = self.source / "00007000"
        pasta.mkdir()
        cabecalho = pasta / "8A1B2C3D"
        StfsBuilder().add_file("default.xex", b"XEX2").build(cabecalho)

        self.assertIs(sniff(cabecalho), Fmt.STFS)

        dados = pasta / "8A1B2C3D.data"
        dados.mkdir()
        (dados / "data0000").write_bytes(b"\0" * 1024)

        self.assertIs(sniff(cabecalho), Fmt.GOD)
        self.assertIs(sniff(pasta), Fmt.GOD)
        self.assertEqual(payload_path(pasta), cabecalho)

    def test_auto_god_reconstroi_e_segue_para_zar(self):
        """A cadeia god -> xiso -> zar monta-se sozinha: três etapas, zero
        código a ligá-las."""
        from core.xbox.god import Layout
        from tests.god_builder import GodBuilder, make_xdvdfs_image

        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.source / "8A1B2C3D", make_xdvdfs_image(80)
        )

        runner = self.build([header])
        etapas = []
        runner.on_item = lambda status: (
            self.items.append(status),
            status.stage_id and etapas.append(status.stage_id),
        )
        result = runner.run()

        self.assertEqual(result.failed, 0)
        self.assertEqual(result.completed, 1)
        self.assertEqual([e for i, e in enumerate(etapas) if i == 0 or etapas[i - 1] != e],
                         ["god", "xiso", "zar"])

    def test_god_usa_o_nome_do_jogo_e_nao_o_do_ficheiro(self):
        """Um GOD chama-se '8A1B2C3D' no disco mas sabe que é o Halo."""
        from core.xbox.god import Layout
        from tests.god_builder import GodBuilder, make_xdvdfs_image

        header = GodBuilder(
            Layout(base=0x2000, lead_sectors=0), display_name="Halo 3"
        ).build(self.source / "8A1B2C3D", make_xdvdfs_image(80))

        result = self.build([header]).run()

        self.assertEqual(result.completed, 1)
        self.assertTrue((self.target / "Halo 3.zar").exists(),
                        sorted(p.name for p in self.target.iterdir()))

    def test_nome_de_dentro_do_pacote_nao_escapa_da_pasta(self):
        """O nome de exibição é escrito por quem empacotou; pode trazer
        barras e não pode chegar a um caminho."""
        from tests.stfs_builder import StfsBuilder

        # Nome hexadecimal de propósito: é o caso em que o nome de dentro do
        # pacote manda, e portanto o único em que ele pode fazer estragos.
        pacote = self.source / "DEADBEEF"
        StfsBuilder(display_name="../../fora").add_file(
            "default.xex", b"XEX2"
        ).build(pacote)

        result = self.build([pacote]).run()

        self.assertEqual(result.completed, 1)
        self.assertFalse((self.target.parent / "fora.zar").exists(),
                         "escapou da pasta de destino")
        escritos = [p.name for p in self.target.iterdir() if p.suffix == ".zar"]
        self.assertEqual(escritos, ["fora.zar"], "as barras tinham de cair")

    def test_god_com_geometria_irreconhecivel_falha_sem_escrever(self):
        """Sem a assinatura XDVDFS, entregar uma imagem seria pior que falhar."""
        from core.xbox.god import Layout
        from tests.god_builder import GodBuilder, make_xdvdfs_image

        imagem = bytearray(make_xdvdfs_image(60))
        imagem[0x10000:0x10000 + 20] = b"\x00" * 20
        header = GodBuilder(Layout(base=0x2000, lead_sectors=0)).build(
            self.source / "C0DEF10E", bytes(imagem)
        )

        result = self.build([header]).run()

        self.assertEqual(result.completed, 0)
        self.assertEqual(list(self.target.glob("*.zar")), [])
        self.assertTrue(header.exists(), "o original tem de sobreviver")
        self.assertEqual(self.leftovers(), [])

    def test_lista_pacote_sem_extensao_e_esconde_o_data(self):
        """Um XBLA não tem sufixo; a pasta .data de um GOD não é um item."""
        from services.file_service import FileService
        from tests.stfs_builder import StfsBuilder

        StfsBuilder().add_file("default.xex", b"XEX2").build(self.source / "C0DEF10E")
        StfsBuilder().add_file("default.xex", b"XEX2").build(self.source / "8A1B2C3D")
        dados = self.source / "8A1B2C3D.data"
        dados.mkdir()
        (dados / "data0000").write_bytes(b"\0" * 1024)
        (self.source / "notas.txt").write_text("nada a ver")

        nomes = sorted(p.name for p in
                       FileService.find_processable_files(str(self.source), Mode.AUTO))
        self.assertIn("C0DEF10E", nomes)
        self.assertIn("8A1B2C3D", nomes)
        self.assertNotIn("8A1B2C3D.data", nomes)
        self.assertNotIn("notas.txt", nomes)

    def test_cancelar_pacote_stfs(self):
        from tests.stfs_builder import StfsBuilder

        pacote = self.source / "Grande"
        builder = StfsBuilder()
        for index in range(40):
            builder.add_file(f"f{index:02d}.bin", os.urandom(4096 * 4))
        builder.build(pacote)

        runner = self.build([pacote])
        runner.cancel()
        result = runner.run()

        self.assertEqual(result.completed, 0)
        self.assertTrue(pacote.exists(), "o original tem de sobreviver")
        self.assertEqual(list(self.target.glob("*.zar")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
