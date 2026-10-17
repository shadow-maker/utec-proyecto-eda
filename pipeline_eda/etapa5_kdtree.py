"""Etapa 5 — Índice multidimensional y KNN exacto (responsable: B).

Estructuras: KD-Tree propio sobre atributos de producto; KNN exacto por
fuerza bruta como línea base (también la usa la etapa 7 para medir recall@K).
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .evento import Producto

Punto = tuple[float, ...]


def vectorizar(p: Producto) -> Punto:
    """Atributos numéricos del producto (p. ej. log(precio), categoría codificada...)."""
    raise NotImplementedError


def knn_exacto(puntos: list[Punto], ids: list[int], q: Punto, k: int) -> list[tuple[float, int]]:
    """Fuerza bruta: (distancia, id) de los k más cercanos a `q`."""
    raise NotImplementedError


class KDTree:
    def construir(self, puntos: list[Punto], ids: list[int]) -> None:
        raise NotImplementedError

    def knn(self, q: Punto, k: int) -> list[tuple[float, int]]:
        raise NotImplementedError

    def rango(self, minimo: Punto, maximo: Punto) -> list[int]:
        raise NotImplementedError


class IndiceKD:
    nombre = "etapa5_kdtree"

    def __init__(self) -> None:
        self.arbol = KDTree()

    def construir(self, productos: Iterable[Producto]) -> None:
        raise NotImplementedError

    def similares(self, product_id: int, k: int) -> list[int]:
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Puntos indexados, profundidad, nodos visitados por consulta."""
        raise NotImplementedError
