"""Tokens de design.

Antes, as quatro paletas estavam duplicadas entre app.py e ui/theme_mac.py --
dois sítios para mudar uma cor. Agora cada tema é um único conjunto de tokens
a partir do qual se geram o QPalette e o QSS.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Tokens:
    name: str
    dark: bool

    bg: str              # fundo da janela
    surface: str         # cartões, painéis
    surface_alt: str     # linhas alternadas, campos
    surface_hover: str
    border: str
    border_strong: str

    text: str
    text_muted: str
    text_inverse: str

    accent: str
    accent_hover: str
    accent_text: str     # texto por cima do acento

    danger: str
    warning: str
    success: str

    radius_sm: int = 6
    radius_md: int = 10
    radius_lg: int = 16
    radius_pill: int = 999

    space: int = 8
    font_family: str = field(default="")

    @property
    def console_bg(self) -> str:
        return self.surface_alt if self.dark else "#12141A"

    @property
    def console_text(self) -> str:
        return self.text if self.dark else "#E6E8EE"


PITCH_BLACK = Tokens(
    name="Preto", dark=True,
    bg="#0B0B0F", surface="#141419", surface_alt="#1C1C24", surface_hover="#23232D",
    border="#2A2A35", border_strong="#3A3A48",
    text="#F2F2F7", text_muted="#9A9AAB", text_inverse="#0B0B0F",
    accent="#8B5CF6", accent_hover="#A78BFA", accent_text="#FFFFFF",
    danger="#EF4444", warning="#F59E0B", success="#22C55E",
)

DAYLIGHT = Tokens(
    name="Branco", dark=False,
    bg="#F6F7F9", surface="#FFFFFF", surface_alt="#EFF1F5", surface_hover="#E6EAF0",
    border="#DFE3EA", border_strong="#C3CAD6",
    text="#16181D", text_muted="#6B7280", text_inverse="#FFFFFF",
    accent="#2563EB", accent_hover="#1D4ED8", accent_text="#FFFFFF",
    danger="#DC2626", warning="#B45309", success="#15803D",
)

STEAM = Tokens(
    name="Steam", dark=True,
    bg="#171D25", surface="#1B2838", surface_alt="#223245", surface_hover="#2A3F57",
    border="#2E4257", border_strong="#3D5875",
    text="#E8F0F7", text_muted="#8CA3B8", text_inverse="#0B1520",
    accent="#66C0F4", accent_hover="#8ED2F8", accent_text="#0B1520",
    danger="#E45B5B", warning="#E0A23C", success="#5BA32B",
)

XBOX = Tokens(
    name="Xbox", dark=True,
    bg="#0D1310", surface="#16211A", surface_alt="#1D2C22", surface_hover="#26392C",
    border="#27402F", border_strong="#365943",
    text="#EAF3EC", text_muted="#93AC9B", text_inverse="#0D1310",
    accent="#107C10", accent_hover="#16A310", accent_text="#FFFFFF",
    danger="#E23C3C", warning="#D79B25", success="#3BB143",
)

THEMES: dict[str, Tokens] = {
    "Preto": PITCH_BLACK,
    "Branco": DAYLIGHT,
    "Steam": STEAM,
    "Xbox": XBOX,
}

DEFAULT_DARK = "Preto"
DEFAULT_LIGHT = "Branco"


def get(name: str) -> Tokens:
    return THEMES.get(name, PITCH_BLACK)
