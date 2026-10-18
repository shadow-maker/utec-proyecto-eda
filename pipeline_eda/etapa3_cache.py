"""Etapa 3 — Almacenamiento, lookup y caché (responsable: C).

Estructuras: hash table propia para el catálogo, LRU (hash + lista doblemente
enlazada) para lookups frecuentes y matriz dispersa usuario × producto.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .evento import Event, Producto


class TablaHash:
    """Tabla hash propia (encadenamiento o direccionamiento abierto) con rehash."""

    """Joaquin"""

    def __init__(self, capacidad_inicial: int = 1024) -> None:
        self.capacidad = capacidad_inicial

    def put(self, clave: Any, valor: Any) -> None:
        raise NotImplementedError

    def get(self, clave: Any, defecto: Any = None) -> Any:
        raise NotImplementedError

    def __contains__(self, clave: Any) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def valores(self) -> Iterator[Any]:
        raise NotImplementedError


class CacheLRU:
    """Caché LRU: get/put O(1) con hash + lista doblemente enlazada."""

    def __init__(self, capacidad: int) -> None:
        self.capacidad = capacidad

    def get(self, clave: Any) -> Any | None:
        raise NotImplementedError

    def put(self, clave: Any, valor: Any) -> None:
        raise NotImplementedError


class MatrizDispersa:
    """Interacciones usuario × producto; solo guarda las celdas no nulas."""

    def incrementar(self, fila: int, columna: int, valor: float = 1.0) -> None:
        raise NotImplementedError

    def valor(self, fila: int, columna: int) -> float:
        raise NotImplementedError

    def fila(self, fila: int) -> dict[int, float]:
        raise NotImplementedError


class CatalogoCache:
    nombre = "etapa3_cache"

    def __init__(self, capacidad_lru: int) -> None:
        self.catalogo = TablaHash()
        self.cache = CacheLRU(capacidad_lru)
        self.interacciones = MatrizDispersa()

    def consumir(self, ev: Event) -> None:
        """Actualiza el catálogo (precio, marca...) y la matriz de interacciones."""
        raise NotImplementedError

    def obtener_producto(self, product_id: int) -> Producto | None:
        """Consulta puntual: primero la LRU, luego la tabla hash."""
        raise NotImplementedError

    def productos(self) -> Iterator[Producto]:
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Productos en catálogo, hit rate de la LRU, celdas no nulas de la matriz."""
        raise NotImplementedError
