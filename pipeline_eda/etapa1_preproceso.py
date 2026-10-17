"""Etapa 1 — Preprocesamiento por lotes (responsable: A).

Estructuras: ordenación eficiente propia + búsqueda binaria para limpiar y
deduplicar.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .evento import Event


def ordenar(items: list[Any], clave: Callable[[Any], Any]) -> list[Any]:
    """Ordenación propia (p. ej. merge sort). Se compara contra sorted() en el informe."""
    raise NotImplementedError


def busqueda_binaria(ordenados: list[Any], objetivo: Any) -> int:
    """Índice de `objetivo` en `ordenados`, o -1 si no está."""
    raise NotImplementedError


class Preprocesador:
    nombre = "etapa1_preproceso"

    def __init__(self, ventana_dedup: int = 100_000) -> None:
        self.ventana_dedup = ventana_dedup  # cuántas claves recientes se recuerdan entre lotes
        self._claves_vistas: list[tuple] = []  # ordenadas, para búsqueda binaria

    @staticmethod
    def clave(ev: Event) -> tuple:
        """Clave que identifica un evento repetido."""
        raise NotImplementedError

    def procesar(self, lote: list[Event]) -> list[Event]:
        """validar → normalizar → ordenar por clave → descartar duplicados."""
        raise NotImplementedError

    def _valido(self, ev: Event) -> bool:
        raise NotImplementedError

    def _normalizar(self, ev: Event) -> Event:
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Eventos recibidos, inválidos y duplicados descartados."""
        raise NotImplementedError
