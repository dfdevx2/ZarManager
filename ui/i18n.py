"""Acesso às traduções a partir da UI."""

from __future__ import annotations

import locales


class Translator:
    def __init__(self, cfg):
        self.cfg = cfg

    @property
    def language(self) -> str:
        return self.cfg.get("language") or locales.DEFAULT_LANGUAGE

    def __call__(self, key: str, fallback: str = "", **args) -> str:
        return locales.get_text(self.language, key, fallback, **args)

    def event(self, event) -> str:
        """Traduz um core.events.Event."""
        return locales.get_text(self.language, event.key, **(event.args or {}))
