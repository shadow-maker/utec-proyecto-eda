"""Etapa 3 — Almacenamiento, lookup y caché.

Estructuras: hash table propia para el catálogo, LRU (hash + lista doblemente
enlazada) para lookups frecuentes y matriz dispersa usuario × producto.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .evento import Event, Producto


class TablaHash:
    """Tabla hash propia con encadenamiento y rehash cuando se supera el factor de carga."""

    def __init__(self, capacidad_inicial: int = 17, factor_max: float = 0.75) -> None:
        self._casilleros: list[list[tuple[Any, Any]]] = [[] for _ in range(capacidad_inicial)]
        self._tamano = 0
        self.factor_max = factor_max  # factor de carga máximo antes de agrandar

    def _indice(self, clave: Any) -> int:
        return hash(clave) % len(self._casilleros)

    def put(self, clave: Any, valor: Any) -> None:
        casillero = self._casilleros[self._indice(clave)]
        for i, (k, _) in enumerate(casillero):
            if k == clave:  # ya estaba: se actualiza el valor
                casillero[i] = (clave, valor)
                return
        casillero.append((clave, valor))  # si el casillero ya tenía otra clave, es una colisión
        self._tamano += 1
        if self._tamano > self.factor_max * len(self._casilleros):
            self._redimensionar(2 * len(self._casilleros) + 1)

    def get(self, clave: Any, defecto: Any = None) -> Any:
        for k, v in self._casilleros[self._indice(clave)]:
            if k == clave:
                return v
        return defecto

    def eliminar(self, clave: Any) -> bool:
        casillero = self._casilleros[self._indice(clave)]
        for i, (k, _) in enumerate(casillero):
            if k == clave:
                del casillero[i]
                self._tamano -= 1
                return True
        return False

    def _redimensionar(self, nueva_capacidad: int) -> None:
        # Cada clave cambia de casillero porque cambia el divisor.
        anteriores = self._casilleros
        self._casilleros = [[] for _ in range(nueva_capacidad)]
        for casillero in anteriores:
            for k, v in casillero:
                self._casilleros[self._indice(k)].append((k, v))

    def __contains__(self, clave: Any) -> bool:
        return any(k == clave for k, _ in self._casilleros[self._indice(clave)])

    def __len__(self) -> int:
        return self._tamano

    def valores(self) -> Iterator[Any]:
        for casillero in self._casilleros:
            for _, v in casillero:
                yield v

    def estadisticas(self) -> dict[str, Any]:
        largos = [len(c) for c in self._casilleros]
        ocupados = [l for l in largos if l > 0]
        return {
            "claves": self._tamano,
            "casilleros": len(largos),
            "factor_de_carga": round(self._tamano / len(largos), 2),
            "largo_promedio_casillero_ocupado": (
                round(sum(ocupados) / len(ocupados), 2) if ocupados else 0
            ),
            "casillero_mas_largo": max(largos),
        }


class _Nodo:
    __slots__ = ("clave", "valor", "anterior", "siguiente")

    def __init__(self, clave: Any = None, valor: Any = None) -> None:
        self.clave, self.valor = clave, valor
        self.anterior: _Nodo | None = None  # más reciente
        self.siguiente: _Nodo | None = None  # más antiguo


class CacheLRU:
    """Caché LRU: get/put O(1) con hash + lista doblemente enlazada."""

    def __init__(self, capacidad: int) -> None:
        self.capacidad = capacidad
        self.mapa = TablaHash()  # clave -> nodo
        self.cabeza, self.cola = _Nodo(), _Nodo()  # centinelas
        self.cabeza.siguiente, self.cola.anterior = self.cola, self.cabeza
        self.aciertos = 0
        self.fallos = 0

    def _desenlazar(self, nodo: _Nodo) -> None:
        nodo.anterior.siguiente, nodo.siguiente.anterior = nodo.siguiente, nodo.anterior

    def _poner_adelante(self, nodo: _Nodo) -> None:
        # Justo después de la cabeza: el más reciente.
        nodo.anterior, nodo.siguiente = self.cabeza, self.cabeza.siguiente
        self.cabeza.siguiente.anterior = nodo
        self.cabeza.siguiente = nodo

    def get(self, clave: Any) -> Any | None:
        nodo = self.mapa.get(clave)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self._desenlazar(nodo)  # acaba de usarse: pasa adelante
        self._poner_adelante(nodo)
        return nodo.valor

    def put(self, clave: Any, valor: Any) -> None:
        nodo = self.mapa.get(clave)
        if nodo is not None:  # ya estaba: actualizar y mover adelante
            nodo.valor = valor
            self._desenlazar(nodo)
            self._poner_adelante(nodo)
            return
        if len(self.mapa) >= self.capacidad:  # llena: sale el más antiguo
            mas_antiguo = self.cola.anterior
            self._desenlazar(mas_antiguo)
            self.mapa.eliminar(mas_antiguo.clave)
        nodo = _Nodo(clave, valor)
        self.mapa.put(clave, nodo)
        self._poner_adelante(nodo)

    def __len__(self) -> int:
        return len(self.mapa)

    def tasa_aciertos(self) -> float | None:
        total = self.aciertos + self.fallos
        return round(self.aciertos / total, 3) if total else None


PESOS = {"view": 1, "cart": 3, "purchase": 5}


class MatrizDispersa:
    """Interacciones usuario × producto; solo guarda las celdas no nulas."""

    def __init__(self) -> None:
        self.filas: dict[int, dict[int, float]] = {}  # user_id -> {product_id: puntaje} (solo lo que no es cero)
        self.no_nulos = 0  # cantidad de celdas que no son cero ("non-zeros")

    def incrementar(self, fila: int, columna: int, valor: float = 1.0) -> None:
        celdas = self.filas.setdefault(fila, {})  # fila del usuario (la crea si no existe)
        if columna not in celdas:
            self.no_nulos += 1  # celda nueva distinta de cero
        celdas[columna] = celdas.get(columna, 0) + valor

    def valor(self, fila: int, columna: int) -> float:
        return self.filas.get(fila, {}).get(columna, 0)

    def fila(self, fila: int) -> dict[int, float]:
        return dict(self.filas.get(fila, {}))

    def a_csr(self):
        """Exporta a formato CSR: (indptr, indices, data, usuarios, productos)."""
        import numpy as np  # solo hace falta al exportar; el pipeline no depende de numpy

        usuarios = list(self.filas)  # fila i = usuarios[i]
        productos = sorted({p for celdas in self.filas.values() for p in celdas})
        col = {p: j for j, p in enumerate(productos)}  # product_id -> número de columna
        indptr, indices, data = [0], [], []
        for u in usuarios:
            for p, w in sorted(self.filas[u].items(), key=lambda x: col[x[0]]):
                indices.append(col[p])
                data.append(w)
            indptr.append(len(data))  # aquí termina la fila de este usuario
        return (
            np.array(indptr, dtype=np.int64),
            np.array(indices, dtype=np.int32),
            np.array(data, dtype=np.float64),
            usuarios,
            productos,
        )


class CatalogoCache:
    nombre = "etapa3_cache"

    def __init__(self, capacidad_lru: int) -> None:
        self.catalogo = TablaHash()
        self.cache = CacheLRU(capacidad_lru)
        self.interacciones = MatrizDispersa()

    def consumir(self, ev: Event) -> None:
        """Actualiza el catálogo (último precio visto) y la matriz de interacciones."""
        producto = self.catalogo.get(ev.product_id)
        if producto is None:
            self.catalogo.put(ev.product_id, Producto.desde_evento(ev))
        else:
            # Se modifica el mismo objeto que guarda la LRU, así la caché nunca queda desactualizada.
            producto.price = ev.price
        self.interacciones.incrementar(ev.user_id, ev.product_id, PESOS[ev.event_type])

    def obtener_producto(self, product_id: int) -> Producto | None:
        """Consulta puntual: primero la LRU, luego la tabla hash."""
        producto = self.cache.get(product_id)
        if producto is None:
            producto = self.catalogo.get(product_id)
            if producto is not None:
                self.cache.put(product_id, producto)
        return producto

    def productos(self) -> Iterator[Producto]:
        return self.catalogo.valores()

    def metricas(self) -> dict[str, Any]:
        """Productos en catálogo, hit rate de la LRU, celdas no nulas de la matriz."""
        return {
            "productos": len(self.catalogo),
            "tasa_aciertos_lru": self.cache.tasa_aciertos(),
            "celdas_no_nulas": self.interacciones.no_nulos,
        }
