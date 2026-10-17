"""Etapa 9 — Servicio y visualización (fila H del plan — todos).

Estructuras: Trie para autocompletado y Top-K con heap de tamaño k. Consume
las salidas de las demás etapas, que el orquestador le pasa al construirlo.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .evento import Alerta, Event

if TYPE_CHECKING:  # solo para anotaciones: el servicio no importa etapas en ejecución
    from .etapa3_cache import CatalogoCache
    from .etapa5_kdtree import IndiceKD
    from .etapa7_similitud import Similitud
    from .etapa8_grafo import GrafoCoCompra


class Trie:
    def insertar(self, palabra: str, peso: int = 1) -> None:
        raise NotImplementedError

    def autocompletar(self, prefijo: str, k: int = 10) -> list[str]:
        """Las k palabras con mayor peso que empiezan con `prefijo`."""
        raise NotImplementedError


class TopK:
    """Mantiene los k elementos de mayor puntaje con un heap de mínimos de tamaño k."""

    def __init__(self, k: int) -> None:
        self.k = k

    def actualizar(self, clave: Any, puntaje: float) -> None:
        raise NotImplementedError

    def top(self) -> list[tuple[Any, float]]:
        raise NotImplementedError


class Servicio:
    nombre = "etapa9_servicio"

    def __init__(
        self,
        catalogo: CatalogoCache,
        indice_kd: IndiceKD,
        similitud: Similitud,
        grafo: GrafoCoCompra,
        k: int = 10,
    ) -> None:
        self.catalogo = catalogo
        self.indice_kd = indice_kd
        self.similitud = similitud
        self.grafo = grafo
        self.trie = Trie()
        self.populares_top = TopK(k)
        self.alertas: list[tuple[Alerta, bool]] = []

    def registrar_evento(self, ev: Event) -> None:
        """Actualiza popularidad (Top-K) y el Trie con nombres de categoría/marca."""
        raise NotImplementedError

    def registrar_alerta(self, alerta: Alerta, confirmada: bool) -> None:
        raise NotImplementedError

    def autocompletar(self, prefijo: str, k: int = 10) -> list[str]:
        raise NotImplementedError

    def populares(self, k: int = 10) -> list[tuple[int, float]]:
        raise NotImplementedError

    def recomendar(self, product_id: int, k: int = 10) -> list[int]:
        """Combina similitud (etapa 7), KD-Tree (etapa 5) y co-compra/PageRank (etapa 8)."""
        raise NotImplementedError

    def dashboard(self, metricas: dict[str, dict[str, Any]]) -> None:
        """Panel de ventas, actividad, alertas y métricas del pipeline."""
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        raise NotImplementedError
