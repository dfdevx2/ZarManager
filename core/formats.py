"""Identificação de formatos por magic bytes.

Porque é que isto existe: no core antigo era a extensão que decidia o fluxo,
e ".iso" é ambíguo -- pode ser Xbox, GameCube, Wii, PS2 ou um ISO9660 comum.
Com PKG/CHD/RVZ no horizonte isso deixa de ser sustentável.

Regra do pipeline: identificar o ficheiro, executar uma etapa, e voltar a
identificar o que saiu. Só olhando para o conteúdo é possível saber o que
havia dentro de um .7z.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

# Ofsets das partições onde vive a assinatura de um disco Xbox/Xbox 360.
# 0x00000000 = XISO já extraído de redump, 0xFD90000 = XGD2,
# 0x02080000 = XGD3, 0x18300000 = XGD1.
XGD_PARTITIONS = (0x00000000, 0xFD90000, 0x02080000, 0x18300000)
XDVDFS_MAGIC = b"MICROSOFT*XBOX*MEDIA"

# Contentores assinados do Xbox 360. Partilham o mesmo cabeçalho: CON  é
# conteúdo assinado pela consola (saves, alguns DLC), LIVE vem da Xbox Live
# (XBLA, DLC, actualizações) e PIRS da rede de distribuição da Microsoft.
STFS_MAGICS = (b"CON ", b"LIVE", b"PIRS")

ARCHIVE_SUFFIXES = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"}
CD_SHEET_SUFFIXES = {".cue", ".gdi", ".ccd", ".toc"}


class Fmt(Enum):
    """Formatos que o planeador sabe consumir ou produzir."""

    ARCHIVE = "archive"          # zip/rar/7z/tar
    GAME_DIR = "game_dir"        # pasta de jogo (entrada do zarchive)
    XISO = "xiso"                # imagem XDVDFS (Xbox / Xbox 360)
    STFS = "stfs"                # pacote XBLA / DLC / actualização (CON/LIVE/PIRS)
    GOD = "god"                  # Games on Demand: cabeçalho + pasta .data
    GC_ISO = "gc_iso"            # GameCube
    WII_ISO = "wii_iso"          # Wii
    ISO9660 = "iso9660"          # ISO genérico (PS2, PC, ...)
    CD_IMAGE = "cd_image"        # cue/gdi + bin
    PKG_PS3 = "pkg_ps3"
    PKG_PS4 = "pkg_ps4"
    ZAR = "zar"
    RVZ = "rvz"
    CHD = "chd"
    UNKNOWN = "unknown"

    @property
    def is_terminal(self) -> bool:
        """Formatos finais: nada a fazer depois de os produzir."""
        return self in {Fmt.ZAR, Fmt.RVZ, Fmt.CHD}


# Rótulos curtos para a UI (a tradução real vive em locales.py).
FMT_LABEL_KEYS = {
    Fmt.ARCHIVE: "fmt_archive",
    Fmt.GAME_DIR: "fmt_game_dir",
    Fmt.XISO: "fmt_xiso",
    Fmt.STFS: "fmt_stfs",
    Fmt.GOD: "fmt_god",
    Fmt.GC_ISO: "fmt_gc_iso",
    Fmt.WII_ISO: "fmt_wii_iso",
    Fmt.ISO9660: "fmt_iso9660",
    Fmt.CD_IMAGE: "fmt_cd_image",
    Fmt.PKG_PS3: "fmt_pkg_ps3",
    Fmt.PKG_PS4: "fmt_pkg_ps4",
    Fmt.ZAR: "fmt_zar",
    Fmt.RVZ: "fmt_rvz",
    Fmt.CHD: "fmt_chd",
    Fmt.UNKNOWN: "fmt_unknown",
}


def _read_at(handle, offset: int, size: int) -> bytes:
    try:
        handle.seek(offset)
        return handle.read(size)
    except OSError:
        return b""


def god_data_dir(header: Path) -> Path | None:
    """Pasta `<cabeçalho>.data` de um Games on Demand, se existir.

    Um GOD e um pacote XBLA têm exactamente o mesmo cabeçalho -- o que os
    distingue é onde estão os dados. No XBLA estão no próprio ficheiro; no GOD
    estão ao lado, partidos em data0000, data0001, ... dentro desta pasta. É
    por isso que a distinção se faz pelo sistema de ficheiros e não pelos
    bytes: um cabeçalho GOD sozinho, sem a pasta, não dá para nada.
    """
    candidate = header.with_name(header.name + ".data")
    try:
        return candidate if candidate.is_dir() else None
    except OSError:
        return None


def _stfs_flavour(path: Path) -> Fmt:
    return Fmt.GOD if god_data_dir(path) is not None else Fmt.STFS


def _sniff_file(path: Path) -> Fmt:
    suffix = path.suffix.lower()

    if suffix in ARCHIVE_SUFFIXES:
        return Fmt.ARCHIVE
    if suffix in CD_SHEET_SUFFIXES:
        return Fmt.CD_IMAGE
    if suffix == ".zar":
        return Fmt.ZAR

    try:
        with path.open("rb") as handle:
            head = handle.read(0x20)
            if not head:
                return Fmt.UNKNOWN

            if head[:4] in STFS_MAGICS:
                return _stfs_flavour(path)

            if head[:8] == b"MComprHD":
                return Fmt.CHD
            if head[:4] == b"RVZ\x01":
                return Fmt.RVZ
            if head[:4] == b"WIA\x01":
                return Fmt.RVZ            # WIA é o antecessor directo do RVZ
            if head[:4] == b"\x7fPKG":
                return Fmt.PKG_PS3
            if head[:4] == b"\x7fCNT":
                return Fmt.PKG_PS4

            # Wii e GameCube: a assinatura está em offsets fixos do header.
            if head[0x18:0x1C] == b"\x5d\x1c\x9e\xa3":
                return Fmt.WII_ISO
            if head[0x1C:0x20] == b"\xc2\x33\x9f\x3d":
                return Fmt.GC_ISO

            for partition in XGD_PARTITIONS:
                if _read_at(handle, partition + 0x10000, len(XDVDFS_MAGIC)) == XDVDFS_MAGIC:
                    return Fmt.XISO

            # ISO9660 clássico: "CD001" no descritor primário de volume.
            if _read_at(handle, 0x8001, 5) == b"CD001":
                return Fmt.ISO9660
    except OSError:
        return Fmt.UNKNOWN

    if suffix == ".iso":
        return Fmt.ISO9660
    return Fmt.UNKNOWN


def _xbox_container(files: list[Path], dirs: list[Path]) -> tuple[Fmt, Path] | None:
    """Reconhece uma pasta que é apenas o invólucro de um contentor do Xbox 360.

    É o que sai de um .zip de XBLA (um ficheiro sem extensão, sozinho) e o que
    o dashboard escreve para um Games on Demand (o cabeçalho mais a pasta
    `.data` ao lado). Sem isto, o sniff da pasta dava GAME_DIR e o planeador
    mandava o contentor inteiro para o zarchive sem o abrir.
    """
    candidates = [(f, _sniff_file(f)) for f in files]
    matches = [(f, fmt) for f, fmt in candidates if fmt in (Fmt.STFS, Fmt.GOD)]
    if len(matches) != 1:
        return None

    header, fmt = matches[0]
    if fmt is Fmt.GOD:
        data = god_data_dir(header)
        extra = [d for d in dirs if data is None or d.name != data.name]
        return (fmt, header) if not extra else None

    return (fmt, header) if not dirs else None


def _sniff_dir(path: Path) -> Fmt:
    """Classifica uma pasta. Se contiver exactamente uma imagem reconhecível,
    a pasta é transparente e devolvemos o formato dessa imagem -- é isto que
    faz `zip -> pasta -> iso -> rvz` funcionar sem código específico."""
    try:
        entries = [entry for entry in path.iterdir() if not entry.name.startswith(".")]
    except OSError:
        return Fmt.GAME_DIR

    files = [entry for entry in entries if entry.is_file()]
    dirs = [entry for entry in entries if entry.is_dir()]

    container = _xbox_container(files, dirs)
    if container is not None:
        return container[0]

    sheets = [f for f in files if f.suffix.lower() in CD_SHEET_SUFFIXES]
    if sheets and not dirs:
        return Fmt.CD_IMAGE

    images = [
        f for f in files
        if f.suffix.lower() in {".iso", ".pkg", ".chd", ".rvz", ".wbfs", ".gcm"}
    ]
    if len(images) == 1 and not dirs:
        inner = _sniff_file(images[0])
        if inner is not Fmt.UNKNOWN:
            return inner

    # Uma pasta com um único subdiretório é quase sempre o wrapper que o
    # empacotador da Scene deixou para trás.
    if len(dirs) == 1 and not files:
        return _sniff_dir(dirs[0])

    return Fmt.GAME_DIR


def sniff(path: Path) -> Fmt:
    """Formato de um caminho, olhando para o conteúdo e não para o nome."""
    try:
        if path.is_dir():
            return _sniff_dir(path)
        if not path.exists():
            return Fmt.UNKNOWN
    except OSError:
        return Fmt.UNKNOWN
    return _sniff_file(path)


def payload_path(path: Path) -> Path:
    """Caminho real a processar depois de um sniff de pasta.

    Se a pasta é apenas um invólucro à volta de uma imagem ou de outra pasta,
    devolve o conteúdo relevante; caso contrário devolve a própria pasta.
    """
    if not path.is_dir():
        return path
    try:
        entries = [entry for entry in path.iterdir() if not entry.name.startswith(".")]
    except OSError:
        return path

    files = [entry for entry in entries if entry.is_file()]
    dirs = [entry for entry in entries if entry.is_dir()]

    if len(dirs) == 1 and not files:
        return payload_path(dirs[0])

    container = _xbox_container(files, dirs)
    if container is not None:
        return container[1]

    sheets = [f for f in files if f.suffix.lower() in CD_SHEET_SUFFIXES]
    if sheets and not dirs:
        return sheets[0]

    images = [
        f for f in files
        if f.suffix.lower() in {".iso", ".pkg", ".chd", ".rvz", ".wbfs", ".gcm"}
    ]
    if len(images) == 1 and not dirs:
        return images[0]

    return path
