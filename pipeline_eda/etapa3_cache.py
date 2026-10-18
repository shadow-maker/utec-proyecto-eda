"""Etapa 3 — Almacenamiento, lookup y caché (responsable: C).

Estructuras: hash table propia para el catálogo, LRU (hash + lista doblemente
enlazada) para lookups frecuentes y matriz dispersa usuario × producto.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .evento import Event, Producto

import numpy as np


class TablaHash:
    """Tabla hash propia (encadenamiento o direccionamiento abierto) con rehash."""

    """Joaquin"""


class HashTable:
    def __init__(self, capacity=17, max_load=0.75):
        # Creamos 'capacity' casilleros vacíos. Cada casillero es una lista.
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0  # cuántas claves hay guardadas
        self.max_load = max_load  # factor de carga máximo antes de agrandar

    def _index(self, key):
        # ¿En qué casillero va esta clave? hash() de Python + resto de la división.
        return hash(key) % len(self._buckets)

    def add(self, key, value):
        bucket = self._buckets[self._index(key)]  # ir al casillero que toca
        for i, (k, _) in enumerate(bucket):  # ¿la clave ya está ahí?
            if k == key:
                bucket[i] = (key, value)  # sí: solo actualizamos el valor
                return
        bucket.append(
            (key, value)
        )  # no: la agregamos al final (si había otra, es una colisión)
        self._size += 1
        # Si hay demasiadas claves por casillero, agrandamos el estante.
        if self._size > self.max_load * len(self._buckets):
            self._resize(2 * len(self._buckets) + 1)

    def lookup(self, key):
        # Ir al casillero y recorrer su (cortísima) lista.
        for k, v in self._buckets[self._index(key)]:
            if k == key:
                return v
        return None  # no estaba

    def remove(self, key):
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def _resize(self, new_capacity):
        # Estante nuevo (más grande) y reubicar cada clave: su casillero cambia
        # porque ahora dividimos por otro número.
        old = self._buckets
        self._buckets = [[] for _ in range(new_capacity)]
        for bucket in old:
            for k, v in bucket:
                self._buckets[self._index(k)].append((k, v))

    def values(self):
        for bucket in self._buckets:
            for _, v in bucket:
                yield v

    def __len__(self):
        return self._size

    def stats(self):
        largos = [len(b) for b in self._buckets]
        ocupados = [l for l in largos if l > 0]
        return {
            "claves": self._size,
            "casilleros": len(largos),
            "factor_de_carga": round(self._size / len(largos), 2),
            "largo_promedio_casillero_ocupado": (
                round(sum(ocupados) / len(ocupados), 2) if ocupados else 0
            ),
            "casillero_mas_largo": max(largos),
        }


class Node:
    # Un elemento de la lista: guarda clave, valor y sus dos vecinos.
    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = None  # vecino de adelante (más reciente)
        self.next = None  # vecino de atrás (más antiguo)


class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = HashTable()  # clave -> nodo (para encontrarlo rápido)
        self.head, self.tail = Node(), Node()  # extremos fijos
        self.head.next, self.tail.prev = self.tail, self.head
        self.hits = 0  # veces que estaba en la caché
        self.misses = 0  # veces que no estaba

    def _unlink(self, node):
        # Sacar un nodo de la lista: sus vecinos se conectan entre sí.
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        # Poner un nodo justo después de head (= el más reciente).
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.lookup(key)
        if node is None:
            self.misses += 1
            return None
        self.hits += 1
        self._unlink(node)  # lo sacamos de donde estaba...
        self._push_front(node)  # ...y lo ponemos adelante: acaba de usarse
        return node.value

    def put(self, key, value):
        node = self.map.lookup(key)
        if node is not None:  # ya estaba: actualizar y mover adelante
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self.map) >= self.capacity:  # 1) compruebo: ¿está llena?
            oldest = self.tail.prev  # 2) elimino al más antiguo
            self._unlink(oldest)
            self.map.remove(oldest.key)
        node = Node(key, value)  # 3) añado el nuevo
        self.map.add(key, node)
        self._push_front(node)

    def hit_rate(self):
        total = self.hits + self.misses
        return round(self.hits / total, 3) if total else None


PESOS = {"view": 1, "cart": 3, "purchase": 5}


class SparseMatrix:
    def __init__(self):
        self.rows = {}  # user_id -> {product_id: puntaje}   (solo lo que no es cero)
        self.nnz = 0  # cantidad de celdas que no son cero ("non-zeros")

    def add(self, user_id, product_id, peso):
        row = self.rows.setdefault(
            user_id, {}
        )  # fila del usuario (la crea si no existe)
        if product_id not in row:
            self.nnz += 1  # celda nueva distinta de cero
        row[product_id] = row.get(product_id, 0) + peso

    def to_csr(self):
        users = list(self.rows)  # fila i = users[i]
        products = sorted({p for row in self.rows.values() for p in row})
        col = {p: j for j, p in enumerate(products)}  # product_id -> número de columna
        indptr, indices, data = [0], [], []
        for u in users:
            for p, w in sorted(self.rows[u].items(), key=lambda x: col[x[0]]):
                indices.append(col[p])
                data.append(w)
            indptr.append(len(data))  # aquí termina la fila de este usuario
        return (
            np.array(indptr, dtype=np.int64),
            np.array(indices, dtype=np.int32),
            np.array(data, dtype=np.int32),
            users,
            products,
        )


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
