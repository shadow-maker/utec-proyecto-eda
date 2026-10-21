"""Etapa 3 — Almacenamiento, lookup y caché (responsable: C).

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
        # Creamos 'capacidad_inicial' casilleros vacíos. Cada casillero es una lista.
        self._casilleros: list[list[tuple[Any, Any]]] = [[] for _ in range(capacidad_inicial)]
        self._tamano = 0  # cuántas claves hay guardadas
        self.factor_max = factor_max  # factor de carga máximo antes de agrandar

    def _indice(self, clave: Any) -> int:
        # ¿En qué casillero va esta clave? hash() de Python + resto de la división.
        return hash(clave) % len(self._casilleros)

    def put(self, clave: Any, valor: Any) -> None:
        casillero = self._casilleros[self._indice(clave)]  # ir al casillero que toca
        for i, (k, _) in enumerate(casillero):  # ¿la clave ya está ahí?
            if k == clave:
                casillero[i] = (clave, valor)  # sí: solo actualizamos el valor
                return
        casillero.append((clave, valor))  # no: la agregamos al final (si había otra, es una colisión)
        self._tamano += 1
        # Si hay demasiadas claves por casillero, agrandamos el estante.
        if self._tamano > self.factor_max * len(self._casilleros):
            self._redimensionar(2 * len(self._casilleros) + 1)

    def get(self, clave: Any, defecto: Any = None) -> Any:
        # Ir al casillero y recorrer su (cortísima) lista.
        for k, v in self._casilleros[self._indice(clave)]:
            if k == clave:
                return v
        return defecto  # no estaba

    def eliminar(self, clave: Any) -> bool:
        casillero = self._casilleros[self._indice(clave)]
        for i, (k, _) in enumerate(casillero):
            if k == clave:
                del casillero[i]
                self._tamano -= 1
                return True
        return False

    def _redimensionar(self, nueva_capacidad: int) -> None:
        # Estante nuevo (más grande) y reubicar cada clave: su casillero cambia
        # porque ahora dividimos por otro número.
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
    # Un elemento de la lista: guarda clave, valor y sus dos vecinos.
    __slots__ = ("clave", "valor", "anterior", "siguiente")

    def __init__(self, clave: Any = None, valor: Any = None) -> None:
        self.clave, self.valor = clave, valor
        self.anterior: _Nodo | None = None  # vecino de adelante (más reciente)
        self.siguiente: _Nodo | None = None  # vecino de atrás (más antiguo)


class CacheLRU:
    """Caché LRU: get/put O(1) con hash + lista doblemente enlazada."""

    def __init__(self, capacidad: int) -> None:
        self.capacidad = capacidad
        self.mapa = TablaHash()  # clave -> nodo (para encontrarlo rápido)
        self.cabeza, self.cola = _Nodo(), _Nodo()  # extremos fijos
        self.cabeza.siguiente, self.cola.anterior = self.cola, self.cabeza
        self.aciertos = 0  # veces que estaba en la caché
        self.fallos = 0  # veces que no estaba

    def _desenlazar(self, nodo: _Nodo) -> None:
        # Sacar un nodo de la lista: sus vecinos se conectan entre sí.
        nodo.anterior.siguiente, nodo.siguiente.anterior = nodo.siguiente, nodo.anterior

    def _poner_adelante(self, nodo: _Nodo) -> None:
        # Poner un nodo justo después de la cabeza (= el más reciente).
        nodo.anterior, nodo.siguiente = self.cabeza, self.cabeza.siguiente
        self.cabeza.siguiente.anterior = nodo
        self.cabeza.siguiente = nodo

    def get(self, clave: Any) -> Any | None:
        nodo = self.mapa.get(clave)
        if nodo is None:
            self.fallos += 1
            return None
        self.aciertos += 1
        self._desenlazar(nodo)  # lo sacamos de donde estaba...
        self._poner_adelante(nodo)  # ...y lo ponemos adelante: acaba de usarse
        return nodo.valor

    def put(self, clave: Any, valor: Any) -> None:
        nodo = self.mapa.get(clave)
        if nodo is not None:  # ya estaba: actualizar y mover adelante
            nodo.valor = valor
            self._desenlazar(nodo)
            self._poner_adelante(nodo)
            return
        if len(self.mapa) >= self.capacidad:  # 1) compruebo: ¿está llena?
            mas_antiguo = self.cola.anterior  # 2) elimino al más antiguo
            self._desenlazar(mas_antiguo)
            self.mapa.eliminar(mas_antiguo.clave)
        nodo = _Nodo(clave, valor)  # 3) añado el nuevo
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
