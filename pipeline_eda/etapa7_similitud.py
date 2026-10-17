"""Etapa 7 [FIJA] — Similitud aproximada (responsable: B).

Estructuras: MinHash + LSH sobre conjuntos (usuarios que compraron o
agregaron al carrito cada producto) y HNSW sobre vectores de producto.
Líneas base: Jaccard por fuerza bruta y KNN exacto de la etapa 5.
"""
from __future__ import annotations

import math
import random
from typing import Any

from .evento import Event

Vector = tuple[float, ...]


def jaccard_exacto(a: set[int], b: set[int]) -> float:
    raise NotImplementedError


class MinHash:
    def __init__(self, num_permutaciones: int = 128, seed: int = 42) -> None:
        self.num_permutaciones = num_permutaciones
        self.seed = seed

    def firma(self, conjunto: set[int]) -> list[int]:
        raise NotImplementedError


class LSH:
    """Divide cada firma en `bandas` de `filas`; candidatos = comparten algún bucket."""

    def __init__(self, bandas: int, filas: int) -> None:
        self.bandas = bandas
        self.filas = filas

    def insertar(self, id_: int, firma: list[int]) -> None:
        raise NotImplementedError

    def candidatos(self, firma: list[int]) -> set[int]:
        raise NotImplementedError


class HNSW:
    def __init__(self, m: int = 16, ef_construccion: int = 200, seed: int = 42) -> None:
        self.m = m
        self.ef_construccion = ef_construccion
        self.seed = seed

    def insertar(self, id_: int, vector: Vector) -> None:
        raise NotImplementedError

    def buscar(self, q: Vector, k: int, ef: int = 50) -> list[tuple[float, int]]:
        raise NotImplementedError


class Similitud:
    nombre = "etapa7_similitud"

    def __init__(self, num_permutaciones: int = 128, bandas: int = 32, seed: int = 42) -> None:
        self.conjuntos: dict[int, set[int]] = {}  # product_id -> usuarios
        self.minhash = MinHash(num_permutaciones, seed)
        self.lsh = LSH(bandas, num_permutaciones // bandas)
        self.hnsw = HNSW(seed=seed)

    def consumir(self, ev: Event) -> None:
        """Acumula el usuario en el conjunto del producto (cart / purchase)."""
        raise NotImplementedError

    def cerrar(self) -> None:
        """Calcula las firmas MinHash e indexa en LSH."""
        raise NotImplementedError

    def construir_vectorial(self, vectores: dict[int, Vector]) -> None:
        """Inserta en HNSW los vectores de producto (los entrega el orquestador)."""
        raise NotImplementedError

    def relacionados(self, product_id: int, k: int) -> list[int]:
        """Productos comprados por usuarios parecidos (MinHash + LSH)."""
        raise NotImplementedError

    def similares_vectoriales(self, product_id: int, k: int) -> list[int]:
        """Productos con atributos parecidos (HNSW)."""
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Candidatos por consulta, recall@K vs. exacto, memoria."""
        raise NotImplementedError
