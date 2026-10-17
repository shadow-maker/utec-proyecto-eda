"""Etapa 4 — Indexación principal (responsable: B).

Estructura: B+Tree propio para un índice de disco (nodos = páginas), con
consultas puntuales y por rango.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from .evento import Event


class BPlusTree:
    """B+Tree de orden `orden`. Las hojas están enlazadas para recorrer rangos.

    Si `ruta` no es None, los nodos se persisten como páginas en ese archivo.
    """

    def __init__(self, orden: int = 64, ruta: Path | str | None = None) -> None:
        self.orden = orden
        self.ruta = ruta

    def insertar(self, clave: Any, valor: Any) -> None:
        raise NotImplementedError

    def buscar(self, clave: Any) -> list[Any]:
        raise NotImplementedError

    def rango(self, desde: Any, hasta: Any) -> Iterator[tuple[Any, Any]]:
        raise NotImplementedError


class IndiceProductos:
    nombre = "etapa4_bplustree"

    def __init__(self, orden: int = 64) -> None:
        self.por_precio = BPlusTree(orden)  # precio -> product_id
        self.por_tiempo = BPlusTree(orden)  # event_time -> evento (o su posición)

    def consumir(self, ev: Event) -> None:
        raise NotImplementedError

    def productos_en_rango_precio(self, desde: float, hasta: float) -> list[int]:
        raise NotImplementedError

    def eventos_en_rango_tiempo(self, desde: int, hasta: int) -> Iterator[Any]:
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Claves indexadas, altura del árbol, páginas leídas por consulta."""
        raise NotImplementedError
