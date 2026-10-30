"""Etapa 5 — KD-Tree y KNN exacto.

Distancia = sqrt(Δprecio_normalizado² + (0 si es la misma categoría, 1 si no)).
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from .evento import Producto

# (precio_normalizado: float, category_id: int)
Punto = tuple[float, int]


def vectorizar(p: Producto, precio_min: float = 0.79,
               precio_max: float = 3000.0) -> Punto:
    """Normaliza precio y conserva el ID de categoría sin pérdida de precisión.

    IndiceKD calcula min/max reales del catálogo y los pasa explícitamente.
    Los valores por defecto sirven para pruebas individuales.
    """
    precio = float(p.price)
    if not math.isfinite(precio) or precio < 0:
        raise ValueError("El precio debe ser finito y no negativo")
    if not (math.isfinite(precio_min) and math.isfinite(precio_max)):
        raise ValueError("Los límites de precio deben ser finitos")
    if precio_max < precio_min:
        raise ValueError("precio_max debe ser >= precio_min")
    if precio_max == precio_min:
        normalizado = 0.0
    else:
        normalizado = (precio - precio_min) / (precio_max - precio_min)
    return (normalizado, int(p.category_id))


def distancia_mixta(a: Punto, b: Punto) -> float:
    """Distancia por precio normalizado y coincidencia exacta de categoría."""
    if len(a) != 2 or len(b) != 2:
        raise ValueError("Cada punto debe contener (precio_normalizado, category_id)")
    diferencia = a[0] - b[0]
    penalizacion = 0 if a[1] == b[1] else 1
    return math.sqrt(diferencia * diferencia + penalizacion)


def knn_exacto(puntos: list[Punto], ids: list[int], q: Punto,
               k: int) -> list[tuple[float, int]]:
    """Fuerza bruta exacta, ordenada por (distancia, product_id)."""
    if len(puntos) != len(ids):
        raise ValueError("puntos e ids deben tener la misma longitud")
    if k <= 0:
        return []
    resultados = [(distancia_mixta(punto, q), product_id)
                  for punto, product_id in zip(puntos, ids)]
    resultados.sort()
    return resultados[:k]


class NodoKD:
    def __init__(self, punto: Punto, product_id: int, eje: int = 0) -> None:
        self.punto = punto
        self.product_id = product_id
        self.eje = eje  # Único eje de partición: precio normalizado
        self.izquierda: NodoKD | None = None
        self.derecha: NodoKD | None = None


class KDTree:
    """Árbol KD de una dimensión (precio) con distancia mixta en KNN.

    La poda usa exclusivamente una cota inferior por diferencia de precio;
    esto es seguro porque la penalización categórica nunca es negativa.
    """

    def __init__(self) -> None:
        self.raiz: NodoKD | None = None
        self.dimension = 2  # Dos atributos, pero solo uno es eje de corte
        self.puntos_indexados = 0
        self.profundidad = 0
        self.nodos_visitados = 0

    def construir(self, puntos: list[Punto], ids: list[int]) -> None:
        if len(puntos) != len(ids):
            raise ValueError("puntos e ids deben tener la misma longitud")
        if any(len(p) != 2 for p in puntos):
            raise ValueError("Los puntos deben ser (precio_normalizado, category_id)")
        if len(set(ids)) != len(ids):
            raise ValueError("Los IDs de producto deben ser únicos")

        self.puntos_indexados = len(puntos)
        self.nodos_visitados = 0
        self.profundidad = 0

        def construir_rec(elementos: list[tuple[Punto, int]],
                         nivel: int) -> NodoKD | None:
            if not elementos:
                return None
            elementos.sort(key=lambda item: (item[0][0], item[1]))
            medio = len(elementos) // 2
            punto, product_id = elementos[medio]
            nodo = NodoKD(punto, product_id)
            self.profundidad = max(self.profundidad, nivel)
            nodo.izquierda = construir_rec(elementos[:medio], nivel + 1)
            nodo.derecha = construir_rec(elementos[medio + 1:], nivel + 1)
            return nodo

        self.raiz = construir_rec(list(zip(puntos, ids)), 1)

    def knn(self, q: Punto, k: int) -> list[tuple[float, int]]:
        self.nodos_visitados = 0
        if k <= 0 or self.raiz is None:
            return []
        if len(q) != 2:
            raise ValueError("La consulta debe tener precio y categoría")

        mejores: list[tuple[float, int]] = []

        def buscar(nodo: NodoKD | None) -> None:
            if nodo is None:
                return
            self.nodos_visitados += 1
            distancia = distancia_mixta(nodo.punto, q)
            mejores.append((distancia, nodo.product_id))
            mejores.sort()
            if len(mejores) > k:
                mejores.pop()

            diferencia = q[0] - nodo.punto[0]
            primero = nodo.izquierda if diferencia <= 0 else nodo.derecha
            segundo = nodo.derecha if diferencia <= 0 else nodo.izquierda
            buscar(primero)

            limite = mejores[-1][0] if len(mejores) == k else math.inf
            # Incluye empates: desempate por ID de producto.
            if abs(diferencia) <= limite:
                buscar(segundo)

        buscar(self.raiz)
        return mejores

    def rango(self, minimo: Punto, maximo: Punto) -> list[int]:
        """Filtra por intervalo de precio y categoría.

        Para categoría idéntica en ambos límites exige esa categoría.
        Si difieren, admite IDs de categoría en el intervalo inclusivo;
        esto es una consulta de rango por ID, NO una medida de similitud.
        """
        if len(minimo) != 2 or len(maximo) != 2:
            raise ValueError("Los límites deben tener precio y categoría")
        if minimo[0] > maximo[0] or minimo[1] > maximo[1]:
            return []
        encontrados: list[int] = []

        def buscar(nodo: NodoKD | None) -> None:
            if nodo is None:
                return
            precio, categoria = nodo.punto
            if minimo[0] <= precio <= maximo[0] and minimo[1] <= categoria <= maximo[1]:
                encontrados.append(nodo.product_id)
            if minimo[0] <= precio:
                buscar(nodo.izquierda)
            if maximo[0] >= precio:
                buscar(nodo.derecha)

        buscar(self.raiz)
        return sorted(encontrados)


class IndiceKD:
    nombre = "etapa5_kdtree"

    def __init__(self) -> None:
        self.arbol = KDTree()
        self.productos: dict[int, Producto] = {}
        self.puntos: list[Punto] = []
        self.ids: list[int] = []
        self.precio_min = 0.0
        self.precio_max = 0.0
        self._puntos_por_id: dict[int, Punto] = {}

    def construir(self, productos: Iterable[Producto]) -> None:
        catalogo = {p.product_id: p for p in productos}
        self.productos = catalogo
        self.ids = sorted(catalogo)
        precios = [float(p.price) for p in catalogo.values()]
        if any(not math.isfinite(p) or p < 0 for p in precios):
            raise ValueError("Todos los precios deben ser finitos y no negativos")
        self.precio_min = min(precios) if precios else 0.0
        self.precio_max = max(precios) if precios else 0.0
        self.puntos = [vectorizar(catalogo[pid], self.precio_min, self.precio_max)
                       for pid in self.ids]
        self._puntos_por_id = dict(zip(self.ids, self.puntos))
        self.arbol.construir(self.puntos, self.ids)

    def similares(self, product_id: int, k: int) -> list[int]:
        if k <= 0 or product_id not in self.productos:
            return []
        q = self._puntos_por_id[product_id]
        vecinos = self.arbol.knn(q, k + 1)
        return [pid for _, pid in vecinos if pid != product_id][:k]

    def metricas(self) -> dict[str, Any]:
        return {
            "puntos_indexados": len(self.ids),
            "profundidad": self.arbol.profundidad,
            "nodos_visitados_ultima_consulta": self.arbol.nodos_visitados,
            "precio_min": self.precio_min,
            "precio_max": self.precio_max,
        }
