"""Etapa 5 — Índice multidimensional y KNN exacto (responsable: B).

Estructuras: KD-Tree propio sobre atributos de producto; KNN exacto por
fuerza bruta como línea base (también la usa la etapa 7 para medir recall@K).
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from .evento import Producto

Punto = tuple[float, ...]

"""CONSTRUCCIÓN DE KNN"""
def vectorizar(p: Producto) -> Punto:
    """Convierte un producto en un vector numérico."""
    precio = max(0.0, p.price)
    return (math.log1p(precio), float(p.category_id))


def knn_exacto(
    puntos: list[Punto],
    ids: list[int],
    q: Punto,
    k: int,
) -> list[tuple[float, int]]:
    """Devuelve los k puntos más cercanos mediante fuerza bruta."""
    if len(puntos) != len(ids):
        raise ValueError("puntos e ids deben tener la misma longitud")

    if k <= 0:
        return []

    resultados: list[tuple[float, int]] = []

    for punto, product_id in zip(puntos, ids):
        if len(punto) != len(q):
            raise ValueError(
                "Todos los vectores deben tener la misma dimensión"
            )

        distancia = math.sqrt(
            sum((a - b) ** 2 for a, b in zip(punto, q))
        )

        resultados.append((distancia, product_id))

    resultados.sort()
    return resultados[:k]

"""CONSTRUCCIÓN DE KD-TREE"""
class NodoKD:
    def __init__(
        self,
        punto: Punto,
        product_id: int,
        eje: int,
    ) -> None:
        self.punto = punto
        self.product_id = product_id
        self.eje = eje
        self.izquierda: NodoKD | None = None
        self.derecha: NodoKD | None = None


class KDTree:
    def __init__(self) -> None:
        self.raiz: NodoKD | None = None
        self.dimension = 0
        self.puntos_indexados = 0
        self.profundidad = 0
        self.nodos_visitados = 0

    def construir(self, puntos: list[Punto], ids: list[int]) -> None:
        if len(puntos) != len(ids):
            raise ValueError("puntos e ids deben tener la misma longitud")

        if puntos and any(len(p) != len(puntos[0]) for p in puntos):
            raise ValueError("Todos los puntos deben tener igual dimensión")

        if len(set(ids)) != len(ids):
            raise ValueError("Los IDs de producto deben ser únicos")

        self.dimension = len(puntos[0]) if puntos else 0
        self.puntos_indexados = len(puntos)
        self.nodos_visitados = 0

        def construir_rec(
            elementos: list[tuple[Punto, int]],
            eje: int,
            nivel: int,
        ) -> NodoKD | None:
            if not elementos:
                return None

            elementos.sort(key=lambda elemento: (elemento[0][eje], elemento[1]))
            medio = len(elementos) // 2
            punto, product_id = elementos[medio]

            nodo = NodoKD(punto, product_id, eje)
            siguiente_eje = (eje + 1) % self.dimension

            nodo.izquierda = construir_rec(
                elementos[:medio], siguiente_eje, nivel + 1
            )
            nodo.derecha = construir_rec(
                elementos[medio + 1:], siguiente_eje, nivel + 1
            )

            self.profundidad = max(self.profundidad, nivel + 1)
            return nodo

        self.profundidad = 0
        self.raiz = (
            construir_rec(list(zip(puntos, ids)), 0, 1)
            if puntos else None
        )

    def knn(self, q: Punto, k: int) -> list[tuple[float, int]]:
        if k <= 0 or self.raiz is None:
            return []

        if len(q) != self.dimension:
            raise ValueError("La consulta tiene una dimensión incorrecta")

        mejores: list[tuple[float, int]] = []
        self.nodos_visitados = 0

        def buscar(nodo: NodoKD | None) -> None:
            if nodo is None:
                return

            self.nodos_visitados += 1

            distancia = math.sqrt(
                sum((a - b) ** 2 for a, b in zip(nodo.punto, q))
            )
            mejores.append((distancia, nodo.product_id))
            mejores.sort()
            if len(mejores) > k:
                mejores.pop()

            diferencia = q[nodo.eje] - nodo.punto[nodo.eje]

            primero = nodo.izquierda if diferencia <= 0 else nodo.derecha
            segundo = nodo.derecha if diferencia <= 0 else nodo.izquierda

            buscar(primero)

            distancia_limite = mejores[-1][0] if len(mejores) == k else math.inf
            if abs(diferencia) <= distancia_limite:
                buscar(segundo)

        buscar(self.raiz)
        return mejores

    def rango(self, minimo: Punto, maximo: Punto) -> list[int]:
        if len(minimo) != self.dimension or len(maximo) != self.dimension:
            raise ValueError("Los límites tienen una dimensión incorrecta")

        if any(a > b for a, b in zip(minimo, maximo)):
            return []

        encontrados: list[int] = []

        def buscar(nodo: NodoKD | None) -> None:
            if nodo is None:
                return

            dentro = all(
                a <= valor <= b
                for valor, a, b in zip(nodo.punto, minimo, maximo)
            )

            if dentro:
                encontrados.append(nodo.product_id)

            eje = nodo.eje

            if minimo[eje] <= nodo.punto[eje]:
                buscar(nodo.izquierda)

            if maximo[eje] >= nodo.punto[eje]:
                buscar(nodo.derecha)

        buscar(self.raiz)
        return sorted(encontrados)

"""IMPLEMENTACIÓN DE INDICE KD"""
class IndiceKD:
    nombre = "etapa5_kdtree"

    def __init__(self) -> None:
        self.arbol = KDTree()
        self.productos: dict[int, Producto] = {}
        self.puntos: list[Punto] = []
        self.ids: list[int] = {}

    def construir(self, productos: Iterable[Producto]) -> None:
        catalogo: dict[int, Producto] = {}

        for producto in productos:
            catalogo[producto.product_id] = producto

        self.productos = catalogo
        self.ids = sorted(catalogo)
        self.puntos = [
            vectorizar(catalogo[product_id])
            for product_id in self.ids
        ]

        self.arbol.construir(self.puntos, self.ids)

    def similares(self, product_id: int, k: int) -> list[int]:
        if product_id not in self.productos:
            return []

        if k <= 0:
            return []

        consulta = vectorizar(self.productos[product_id])

        # Se solicita k + 1 porque el producto consultado
        # normalmente aparece como su propio vecino.
        vecinos = self.arbol.knn(consulta, k + 1)

        return [
            vecino_id
            for _, vecino_id in vecinos
            if vecino_id != product_id
        ][:k]

    def metricas(self) -> dict[str, Any]:
        return {
            "puntos_indexados": len(self.ids),
            "profundidad": self.arbol.profundidad,
            "nodos_visitados_ultima_consulta": self.arbol.nodos_visitados,
        }