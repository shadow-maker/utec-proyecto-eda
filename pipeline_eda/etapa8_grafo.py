"""Etapa 8 [FIJA] — Grafo de dominio (responsable: C).

Nodos = productos; arista ponderada = cuántas veces se compraron en la misma
orden. Influencia con PageRank (vs. ranking por grado) y comunidades con
Louvain o Label Propagation (vs. alternativa simple).
"""
from __future__ import annotations

import random
from typing import Any

from .evento import Event


class GrafoCoCompra:
    nombre = "etapa8_grafo"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.adyacencia: dict[int, dict[int, float]] = {}
        self._ordenes: dict[str, set[int]] = {}  # order_id -> productos ya vistos

    def consumir(self, ev: Event) -> None:
        """En cada purchase, conecta el producto con los ya comprados en la misma orden."""
        raise NotImplementedError

    def pagerank(
        self, amortiguacion: float = 0.85, max_iter: int = 100, tol: float = 1e-6
    ) -> dict[int, float]:
        raise NotImplementedError

    def ranking_por_grado(self) -> list[tuple[int, float]]:
        """Línea base: grado ponderado de cada producto, de mayor a menor."""
        raise NotImplementedError

    def comunidades(self, metodo: str = "louvain") -> dict[int, int]:
        """product_id -> id de comunidad."""
        raise NotImplementedError

    def modularidad(self, particion: dict[int, int]) -> float:
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Nodos, aristas, número y tamaño de comunidades, modularidad."""
        raise NotImplementedError
