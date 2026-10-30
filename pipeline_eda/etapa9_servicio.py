"""Etapa 9 — Servicio y visualización.

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


class _NodoTrie:
    __slots__ = ("hijos", "peso", "es_palabra")

    def __init__(self) -> None:
        self.hijos: dict[str, _NodoTrie] = {}
        self.peso = 0
        self.es_palabra = False


class Trie:
    """Árbol de prefijos: cada arista es un carácter y cada palabra termina en un nodo marcado."""

    def __init__(self) -> None:
        self.raiz = _NodoTrie()
        self.palabras = 0

    def insertar(self, palabra: str, peso: int = 1) -> None:
        """Recorre o crea un nodo por carácter y suma `peso` al nodo final. O(largo de la palabra)."""
        nodo = self.raiz
        for c in palabra:
            nodo = nodo.hijos.setdefault(c, _NodoTrie())
        if not nodo.es_palabra:
            nodo.es_palabra = True
            self.palabras += 1
        nodo.peso += peso

    def autocompletar(self, prefijo: str, k: int = 10) -> list[str]:
        """Las k palabras con mayor peso que empiezan con `prefijo`.

        Baja al nodo del prefijo en O(largo del prefijo) y recorre todo su subárbol: O(S + m log m),
        con S nodos en el subárbol y m palabras encontradas.
        """
        nodo = self.raiz
        for c in prefijo:
            nodo = nodo.hijos.get(c)
            if nodo is None:
                return []
        encontradas = []
        pila = [(nodo, prefijo)]
        while pila:
            nodo, palabra = pila.pop()
            if nodo.es_palabra:
                encontradas.append((-nodo.peso, palabra))
            for c, hijo in nodo.hijos.items():
                pila.append((hijo, palabra + c))
        encontradas.sort()  # mayor peso primero; a igual peso, orden alfabético
        return [palabra for _, palabra in encontradas[:k]]


class TopK:
    """Mantiene los k elementos de mayor puntaje con un heap de mínimos de tamaño k.

    La raíz es el menor de los k. `posicion` guarda dónde está cada clave en el heap,
    para poder actualizar un puntaje que ya está adentro. Supone puntajes que solo crecen
    (conteos), así que un elemento que salió puede volver a entrar con su puntaje actual.
    """

    def __init__(self, k: int) -> None:
        self.k = k
        self.heap: list[tuple[float, Any]] = []  # (puntaje, clave)
        self.posicion: dict[Any, int] = {}  # clave -> índice en heap

    def actualizar(self, clave: Any, puntaje: float) -> None:
        """O(log k): actualiza si ya está; si no, entra cuando supera al menor de los k."""
        if clave in self.posicion:
            i = self.posicion[clave]
            self.heap[i] = (puntaje, clave)
            self._bajar(i)  # el puntaje solo crece: en un heap de mínimos el elemento baja
        elif len(self.heap) < self.k:
            self.heap.append((puntaje, clave))
            self.posicion[clave] = len(self.heap) - 1
            self._subir(len(self.heap) - 1)
        elif (puntaje, clave) > self.heap[0]:
            del self.posicion[self.heap[0][1]]  # sale el menor de los k
            self.heap[0] = (puntaje, clave)
            self.posicion[clave] = 0
            self._bajar(0)

    def top(self) -> list[tuple[Any, float]]:
        """Los k elementos, de mayor a menor puntaje. O(k log k)."""
        return [(clave, puntaje) for puntaje, clave in sorted(self.heap, reverse=True)]

    def _intercambiar(self, i: int, j: int) -> None:
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.posicion[self.heap[i][1]] = i
        self.posicion[self.heap[j][1]] = j

    def _subir(self, i: int) -> None:
        while i > 0 and self.heap[i] < self.heap[(i - 1) // 2]:
            self._intercambiar(i, (i - 1) // 2)
            i = (i - 1) // 2

    def _bajar(self, i: int) -> None:
        n = len(self.heap)
        while True:
            menor = i
            for hijo in (2 * i + 1, 2 * i + 2):
                if hijo < n and self.heap[hijo] < self.heap[menor]:
                    menor = hijo
            if menor == i:
                return
            self._intercambiar(i, menor)
            i = menor


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
        self.ventas: dict[int, int] = {}  # product_id -> unidades vendidas
        self.ingresos = 0.0
        self.eventos_por_tipo: dict[str, int] = {}
        self._terminos: set[str] = set()  # marcas y categorías que ya están en el Trie

    def registrar_evento(self, ev: Event) -> None:
        """Actualiza popularidad (Top-K) y el Trie con nombres de categoría/marca.

        Una marca o categoría entra al Trie la primera vez que aparece, y su peso son las ventas.
        """
        self.eventos_por_tipo[ev.event_type] = self.eventos_por_tipo.get(ev.event_type, 0) + 1
        venta = ev.event_type == "purchase"
        for termino in (ev.brand, ev.category_code):
            if termino is not None and (venta or termino not in self._terminos):
                self.trie.insertar(termino, 1 if venta else 0)
                self._terminos.add(termino)
        if venta:
            self.ventas[ev.product_id] = self.ventas.get(ev.product_id, 0) + 1
            self.ingresos += ev.price
            self.populares_top.actualizar(ev.product_id, self.ventas[ev.product_id])

    def registrar_alerta(self, alerta: Alerta, confirmada: bool) -> None:
        self.alertas.append((alerta, confirmada))

    def autocompletar(self, prefijo: str, k: int = 10) -> list[str]:
        """Marcas y categorías que empiezan con `prefijo`, de más a menos vendidas."""
        return self.trie.autocompletar(prefijo.strip().lower(), k)

    def populares(self, k: int = 10) -> list[tuple[int, float]]:
        """Productos más vendidos (a lo más los k del Top-K)."""
        return self.populares_top.top()[:k]

    def recomendar(self, product_id: int, k: int = 10) -> list[int]:
        """Combina similitud (etapa 7), KD-Tree (etapa 5) y co-compra/PageRank (etapa 8).

        En orden de prioridad y sin repetir: productos comprados en la misma orden (por peso),
        productos con compradores parecidos (LSH) y productos de atributos parecidos (KD-Tree).
        """
        vecinos = self.grafo.adyacencia.get(product_id, {})
        co_compra = sorted(vecinos, key=lambda v: (-vecinos[v], v))
        recomendados: list[int] = []
        for fuente in (co_compra, self.similitud.relacionados(product_id, k), self.indice_kd.similares(product_id, k)):
            for pid in fuente:
                if pid != product_id and pid not in recomendados:
                    recomendados.append(pid)
                    if len(recomendados) == k:
                        return recomendados
        return recomendados

    def dashboard(self, metricas: dict[str, dict[str, Any]]) -> None:
        """Panel de ventas, actividad, alertas y métricas del pipeline."""
        confirmadas = sum(confirmada for _, confirmada in self.alertas)
        por_motivo: dict[str, int] = {}
        for alerta, confirmada in self.alertas:
            if confirmada:
                por_motivo[alerta.tipo] = por_motivo.get(alerta.tipo, 0) + 1
        pagerank = self.grafo.pagerank()
        influyentes = sorted(pagerank, key=lambda p: (-pagerank[p], p))[:5]

        print("=== Ventas ===")
        print(f"unidades {sum(self.ventas.values()):,}  ingresos {self.ingresos:,.2f}  productos vendidos {len(self.ventas):,}")
        print("más vendidos:")
        for pid, n in self.populares(5):
            p = self.catalogo.obtener_producto(pid)  # consulta puntual a la etapa 3 (LRU + hash)
            print(f"  {pid} {p.brand or '—'} · {p.category_code or 'sin categoría'} · {p.price:.2f}  ({int(n)} unidades)")
        print("más influyentes (PageRank):", ", ".join(str(pid) for pid in influyentes))
        print("=== Actividad ===")
        print("  ".join(f"{tipo} {n:,}" for tipo, n in sorted(self.eventos_por_tipo.items())))
        print("=== Alertas ===")
        print(f"emitidas {len(self.alertas):,}  bloqueadas {confirmadas:,} {por_motivo}  "
              f"liberadas (falso positivo) {len(self.alertas) - confirmadas:,}")
        print("=== Métricas por etapa ===")
        for etapa, valores in metricas.items():
            print(f"{etapa}: {valores}")

    def metricas(self) -> dict[str, Any]:
        """Eventos, ventas, términos del Trie y alertas registradas."""
        return {
            "eventos": sum(self.eventos_por_tipo.values()),
            "unidades_vendidas": sum(self.ventas.values()),
            "ingresos": round(self.ingresos, 2),
            "terminos_trie": self.trie.palabras,
            "alertas": len(self.alertas),
            "alertas_confirmadas": sum(confirmada for _, confirmada in self.alertas),
        }
