
import random
from collections import defaultdict
import heapq
import random

from .etapa5_kdtree import distancia_mixta, knn_exacto

PRIMO = 2**61 - 1


def jaccard_exacto(a: set[int], b: set[int]) -> float:
    """Similitud exacta entre dos conjuntos."""
    if not a and not b:
        return 1.0

    union = a | b
    return len(a & b) / len(union)


class MinHash:
    def __init__(
        self,
        num_permutaciones: int = 128,
        seed: int = 42
    ) -> None:

        if num_permutaciones <= 0:
            raise ValueError("num_permutaciones debe ser positivo")

        self.num_permutaciones = num_permutaciones
        self.seed = seed

        rng = random.Random(seed)

        # Generamos funciones hash reproducibles.
        self.funciones_hash = [
            (
                rng.randrange(1, PRIMO),
                rng.randrange(PRIMO)
            )
            for _ in range(num_permutaciones)
        ]

    def firma(self, conjunto: set[int]) -> list[int]:
        """Genera una firma MinHash para un conjunto."""

        if not conjunto:
            return [PRIMO] * self.num_permutaciones

        firma = [PRIMO] * self.num_permutaciones

        for elemento in conjunto:
            x = int(elemento) % PRIMO

            for i, (a, b) in enumerate(self.funciones_hash):

                valor_hash = (a * x + b) % PRIMO

                if valor_hash < firma[i]:
                    firma[i] = valor_hash

        return firma


class LSH:
    """Divide firmas MinHash en bandas y filas."""

    def __init__(self, bandas: int, filas: int) -> None:

        if bandas <= 0 or filas <= 0:
            raise ValueError("bandas y filas deben ser positivos")

        self.bandas = bandas
        self.filas = filas

        self.buckets = defaultdict(set)
        self.firmas = {}

    def _obtener_bandas(self, firma: list[int]):

        if len(firma) != self.bandas * self.filas:
            raise ValueError(
                "La firma debe tener bandas * filas elementos"
            )

        for banda in range(self.bandas):

            inicio = banda * self.filas
            fin = inicio + self.filas

            clave = (banda, tuple(firma[inicio:fin]))

            yield clave

    def insertar(self, id_: int, firma: list[int]) -> None:
        """Guarda un producto en los buckets correspondientes."""

        if id_ in self.firmas:
            firma_anterior = self.firmas[id_]

            for clave in self._obtener_bandas(firma_anterior):
                self.buckets[clave].discard(id_)

        self.firmas[id_] = list(firma)

        for clave in self._obtener_bandas(firma):
            self.buckets[clave].add(id_)

    def candidatos(self, firma: list[int]) -> set[int]:
        """Recupera productos que comparten alguna banda."""

        resultado = set()

        for clave in self._obtener_bandas(firma):
            resultado.update(self.buckets.get(clave, set()))

        return resultado



    def consumir(self, ev: Event) -> None:
        """Registra usuarios que compraron o agregaron al carrito."""

        if ev.event_type not in ("cart", "purchase", "add_to_cart"):
            return

        if ev.user_id is None or ev.product_id is None:
            return

        producto = int(ev.product_id)
        usuario = int(ev.user_id)

        if producto not in self.conjuntos:
            self.conjuntos[producto] = set()

        self.conjuntos[producto].add(usuario)

    def cerrar(self) -> None:
        """Construye firmas MinHash y el índice LSH."""

        self.lsh = LSH(
            self.lsh.bandas,
            self.lsh.filas
        )

        self.firmas_productos = {}

        for producto, usuarios in self.conjuntos.items():

            firma = self.minhash.firma(usuarios)

            self.firmas_productos[producto] = firma

            self.lsh.insertar(producto, firma)

    def relacionados(self, product_id: int, k: int) -> list[int]:
        """Encuentra productos con compradores similares."""

        if k <= 0 or product_id not in self.conjuntos:
            return []

        if not hasattr(self, "firmas_productos"):
            self.cerrar()

        firma = self.firmas_productos[product_id]

        candidatos = self.lsh.candidatos(firma)

        candidatos.discard(product_id)

        # Ordenamos los candidatos por Jaccard exacto.
        resultados = []

        for candidato in candidatos:

            similitud = jaccard_exacto(
                self.conjuntos[product_id],
                self.conjuntos[candidato]
            )

            resultados.append((similitud, candidato))

        resultados.sort(key=lambda x: (-x[0], x[1]))

        return [producto for _, producto in resultados[:k]]



class HNSW:
   import heapq
import math
import random

class HNSW:
    """HNSW educativo: capas jerárquicas, búsqueda ef y selección diversificada."""

    def __init__(self, m: int = 16, ef_construccion: int = 200, seed: int = 42) -> None:
        if m < 2 or ef_construccion < 1:
            raise ValueError('m debe ser >= 2 y ef_construccion >= 1')
        self.m = m
        self.ef_construccion = max(ef_construccion, m)
        self.seed = seed
        self.rng = random.Random(seed)
        self.vectores = {}
        self.niveles = {}
        self.grafo = {}
        self.entrada = None
        self.nivel_maximo = -1
        self.nodos_visitados = 0

    def _distancia(self, q, id_):
        return distancia_mixta(q, self.vectores[id_])

    def _nivel_aleatorio(self):
        nivel = 0
        while nivel < 32 and self.rng.random() < 1 / self.m:
            nivel += 1
        return nivel

    def _busqueda_voraz(self, q, actual, nivel):
        mejor = self._distancia(q, actual)
        while True:
            siguiente = actual
            for vecino in self.grafo[actual][nivel]:
                d = self._distancia(q, vecino)
                if (d, vecino) < (mejor, siguiente):
                    mejor, siguiente = d, vecino
            if siguiente == actual:
                return actual
            actual = siguiente

    def _buscar_capa(self, q, entradas, ef, nivel):
        visitados = set(entradas)
        pendientes = [(self._distancia(q, i), i) for i in entradas]
        heapq.heapify(pendientes)
        mejores = [(-d, -i) for d, i in pendientes]
        heapq.heapify(mejores)
        while pendientes:
            d_actual, actual = heapq.heappop(pendientes)
            peor = (-mejores[0][0], -mejores[0][1])
            if len(mejores) >= ef and (d_actual, actual) > peor:
                break
            for vecino in self.grafo[actual][nivel]:
                if vecino in visitados:
                    continue
                visitados.add(vecino)
                d = self._distancia(q, vecino)
                if len(mejores) < ef or (d, vecino) < peor:
                    heapq.heappush(pendientes, (d, vecino))
                    heapq.heappush(mejores, (-d, -vecino))
                    if len(mejores) > ef:
                        heapq.heappop(mejores)
                    peor = (-mejores[0][0], -mejores[0][1])
        self.nodos_visitados += len(visitados)
        return sorted((-d, -i) for d, i in mejores)

    def _seleccionar_vecinos(self, origen, candidatos, max_vecinos):
        """Heurística HNSW: diversifica conexiones, con relleno por cercanía."""
        candidatos = sorted(set(candidatos), key=lambda i: (self._distancia(self.vectores[origen], i), i))
        seleccionados = []
        descartados = []
        for candidato in candidatos:
            dc = self._distancia(self.vectores[origen], candidato)
            if all(distancia_mixta(self.vectores[candidato], self.vectores[s]) >= dc for s in seleccionados):
                seleccionados.append(candidato)
            else:
                descartados.append(candidato)
            if len(seleccionados) == max_vecinos:
                return seleccionados
        for candidato in descartados:
            seleccionados.append(candidato)
            if len(seleccionados) == max_vecinos:
                break
        return seleccionados

    def _recortar(self, id_, capa):
        vecinos = self.grafo[id_][capa]
        if len(vecinos) <= self.m:
            return
        mantener = set(self._seleccionar_vecinos(id_, vecinos, self.m))
        for eliminado in vecinos - mantener:
            self.grafo[eliminado][capa].discard(id_)
        self.grafo[id_][capa] = mantener

    def insertar(self, id_: int, vector) -> None:
        if id_ in self.vectores:
            raise ValueError(f'Producto duplicado: {id_}')
        if len(vector) != 2 or not math.isfinite(float(vector[0])):
            raise ValueError('Vector inválido: (precio_normalizado, category_id)')
        vector = (float(vector[0]), int(vector[1]))
        nivel = self._nivel_aleatorio()
        self.vectores[id_] = vector
        self.niveles[id_] = nivel
        self.grafo[id_] = {capa: set() for capa in range(nivel + 1)}
        if self.entrada is None:
            self.entrada = id_
            self.nivel_maximo = nivel
            return
        actual = self.entrada
        for capa in range(self.nivel_maximo, nivel, -1):
            actual = self._busqueda_voraz(vector, actual, capa)
        for capa in range(min(nivel, self.nivel_maximo), -1, -1):
            candidatos = self._buscar_capa(vector, [actual], self.ef_construccion, capa)
            vecinos = self._seleccionar_vecinos(id_, [i for _, i in candidatos if i != id_], self.m)
            for vecino in vecinos:
                self.grafo[id_][capa].add(vecino)
                self.grafo[vecino][capa].add(id_)
            for vecino in vecinos:
                self._recortar(vecino, capa)
            if candidatos:
                actual = candidatos[0][1]
        if nivel > self.nivel_maximo:
            self.entrada = id_
            self.nivel_maximo = nivel

    def buscar(self, q, k: int, ef: int = 50):
        self.nodos_visitados = 0
        if k <= 0 or self.entrada is None:
            return []
        if len(q) != 2:
            raise ValueError('Consulta inválida')
        actual = self.entrada
        for capa in range(self.nivel_maximo, 0, -1):
            actual = self._busqueda_voraz(q, actual, capa)
        return self._buscar_capa(q, [actual], max(ef, k), 0)[:k]

