"""Etapa 4 — Indexación principal mediante árboles B+."""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from .evento import Event


class BPlusTree:
    """Árbol B+ con hojas enlazadas y consultas por rango."""

    class _Nodo:
        def __init__(self, hoja: bool = True) -> None:
            self.hoja = hoja
            self.claves: list[Any] = []

            # En las hojas: una lista de valores por cada clave.
            self.valores: list[list[Any]] = []

            # En los nodos internos: referencias a los hijos.
            self.hijos: list[Any] = []

            # Enlace a la siguiente hoja.
            self.siguiente: Any = None

    def __init__(
        self,
        orden: int = 64,
        ruta: Path | str | None = None,
    ) -> None:
        if orden < 3:
            raise ValueError("El orden del árbol debe ser como mínimo 3.")

        self.orden = orden
        self.ruta = ruta
        self.max_claves = orden - 1

        self.raiz = self._Nodo()

        # Métricas de consultas.
        self._paginas_leidas_ultima_consulta = 0
        self._paginas_leidas_total = 0
        self._consultas = 0

    def _buscar_hoja(self, clave: Any) -> Any:
        """Encuentra la hoja donde debe estar una clave."""
        nodo = self.raiz

        while True:
            self._paginas_leidas_ultima_consulta += 1

            if nodo.hoja:
                return nodo

            # Las claves internas indican dónde comienza cada hijo.
            posicion = bisect_right(nodo.claves, clave)
            nodo = nodo.hijos[posicion]

    def _registrar_consulta(self) -> None:
        self._paginas_leidas_ultima_consulta = 0
        self._consultas += 1

    def _finalizar_consulta(self) -> None:
        self._paginas_leidas_total += (
            self._paginas_leidas_ultima_consulta
        )

    def insertar(self, clave: Any, valor: Any) -> None:
        """Inserta un valor asociado a una clave."""
        paginas = self._paginas_leidas_ultima_consulta
        hoja = self._buscar_hoja(clave)
        self._paginas_leidas_ultima_consulta = paginas  # una inserción no es una consulta
        posicion = bisect_left(hoja.claves, clave)

        if (
            posicion < len(hoja.claves)
            and hoja.claves[posicion] == clave
        ):
            # La clave ya existe: permite varios valores para ella.
            hoja.valores[posicion].append(valor)
            return

        hoja.claves.insert(posicion, clave)
        hoja.valores.insert(posicion, [valor])

        if len(hoja.claves) > self.max_claves:
            self._dividir_hoja(hoja)

    def _dividir_hoja(self, hoja: Any) -> None:
        """Divide una hoja cuando supera su capacidad."""
        nueva = self._Nodo(hoja=True)
        mitad = len(hoja.claves) // 2

        nueva.claves = hoja.claves[mitad:]
        nueva.valores = hoja.valores[mitad:]

        hoja.claves = hoja.claves[:mitad]
        hoja.valores = hoja.valores[:mitad]

        # Conserva la cadena de hojas para recorrer rangos.
        nueva.siguiente = hoja.siguiente
        hoja.siguiente = nueva

        # La primera clave de la nueva hoja se promociona.
        clave_promovida = nueva.claves[0]
        self._insertar_en_padre(
            hoja,
            clave_promovida,
            nueva,
        )

    def _insertar_en_padre(
        self,
        izquierda: Any,
        clave: Any,
        derecha: Any,
    ) -> None:
        """Inserta una nueva separación en el padre."""
        if izquierda is self.raiz:
            nueva_raiz = self._Nodo(hoja=False)
            nueva_raiz.claves = [clave]
            nueva_raiz.hijos = [izquierda, derecha]
            self.raiz = nueva_raiz
            return

        padre = self._buscar_padre(self.raiz, izquierda)

        posicion = padre.hijos.index(izquierda)
        padre.claves.insert(posicion, clave)
        padre.hijos.insert(posicion + 1, derecha)

        if len(padre.claves) > self.max_claves:
            self._dividir_interno(padre)

    def _buscar_padre(
        self,
        nodo: Any,
        objetivo: Any,
    ) -> Any:
        """Busca el padre de un nodo."""
        if nodo.hoja:
            return None

        if objetivo in nodo.hijos:
            return nodo

        for hijo in nodo.hijos:
            if not hijo.hoja:
                padre = self._buscar_padre(hijo, objetivo)

                if padre is not None:
                    return padre

        return None

    def _dividir_interno(self, nodo: Any) -> None:
        """Divide un nodo interno cuando se llena."""
        nueva = self._Nodo(hoja=False)
        mitad = len(nodo.claves) // 2

        clave_promovida = nodo.claves[mitad]

        nueva.claves = nodo.claves[mitad + 1:]
        nueva.hijos = nodo.hijos[mitad + 1:]

        nodo.claves = nodo.claves[:mitad]
        nodo.hijos = nodo.hijos[:mitad + 1]

        self._insertar_en_padre(
            nodo,
            clave_promovida,
            nueva,
        )

    def buscar(self, clave: Any) -> list[Any]:
        """Devuelve todos los valores asociados a una clave."""
        self._registrar_consulta()

        try:
            hoja = self._buscar_hoja(clave)
            posicion = bisect_left(hoja.claves, clave)

            if (
                posicion < len(hoja.claves)
                and hoja.claves[posicion] == clave
            ):
                return list(hoja.valores[posicion])

            return []
        finally:
            self._finalizar_consulta()

    def rango(
        self,
        desde: Any,
        hasta: Any,
    ) -> Iterator[tuple[Any, Any]]:
        """Recorre las claves dentro del rango, ambos extremos incluidos."""
        if desde > hasta:
            return

        self._registrar_consulta()

        try:
            hoja = self._buscar_hoja(desde)
            posicion = bisect_left(hoja.claves, desde)
            primera_hoja = True

            while hoja is not None:
                # La primera hoja ya fue contada al buscarla.
                if not primera_hoja:
                    self._paginas_leidas_ultima_consulta += 1

                primera_hoja = False

                while posicion < len(hoja.claves):
                    clave = hoja.claves[posicion]

                    if clave > hasta:
                        return

                    for valor in hoja.valores[posicion]:
                        yield clave, valor

                    posicion += 1

                hoja = hoja.siguiente
                posicion = 0

        finally:
            self._finalizar_consulta()

    def _contar_claves(self) -> int:
        """Cuenta las claves distintas almacenadas."""
        cantidad = 0
        hoja = self.raiz

        while not hoja.hoja:
            hoja = hoja.hijos[0]

        while hoja is not None:
            cantidad += len(hoja.claves)
            hoja = hoja.siguiente

        return cantidad

    def _altura(self) -> int:
        """Devuelve el número de niveles del árbol."""
        altura = 1
        nodo = self.raiz

        while not nodo.hoja:
            altura += 1
            nodo = nodo.hijos[0]

        return altura

    def metricas(self) -> dict[str, Any]:
        """Devuelve métricas básicas del árbol."""
        return {
            "claves_indexadas": self._contar_claves(),
            "altura": self._altura(),
            "consultas": self._consultas,
            "paginas_leidas_ultima_consulta":
                self._paginas_leidas_ultima_consulta,
            "paginas_leidas_total": self._paginas_leidas_total,
        }


class IndiceProductos:
    """Índices de productos por precio y eventos por tiempo."""

    nombre = "etapa4_bplustree"

    def __init__(self, orden: int = 64) -> None:
        self.por_precio = BPlusTree(orden)
        self.por_tiempo = BPlusTree(orden)

        # Permite identificar cambios de precio y evitar
        # insertar repetidamente el mismo producto al mismo precio.
        self._precio_actual: dict[int, float] = {}

        self._eventos_procesados = 0

    def consumir(self, ev: Event) -> None:
        """Incorpora un evento a los índices."""
        self._eventos_procesados += 1

        product_id = int(ev.product_id)
        precio = float(ev.price)
        tiempo = ev.event_time

        # Solo indexamos precios válidos y no negativos.
        if precio >= 0:
            precio_anterior = self._precio_actual.get(product_id)

            if precio_anterior != precio:
                self.por_precio.insertar(precio, product_id)
                self._precio_actual[product_id] = precio

        # Se guarda cada evento, incluso si comparte hora con otros.
        self.por_tiempo.insertar(tiempo, ev)

    def productos_en_rango_precio(
        self,
        desde: float,
        hasta: float,
    ) -> list[int]:
        """Devuelve productos cuyo precio actual está en el rango."""
        if desde > hasta:
            return []

        productos: set[int] = set()

        for precio_indexado, product_id in self.por_precio.rango(
            desde,
            hasta,
        ):
            # Un producto puede haber cambiado de precio.
            # Se descartan sus registros de precios anteriores.
            if self._precio_actual.get(product_id) == precio_indexado:
                productos.add(product_id)

        return sorted(productos)

    def eventos_en_rango_tiempo(
        self,
        desde: datetime,
        hasta: datetime,
    ) -> Iterator[Any]:
        """Devuelve los eventos dentro del intervalo de tiempo."""
        if desde > hasta:
            return

        for _, evento in self.por_tiempo.rango(desde, hasta):
            yield evento

    def metricas(self) -> dict[str, Any]:
        """Devuelve métricas de ambos índices."""
        return {
            "eventos_procesados": self._eventos_procesados,
            "productos_indexados": len(self._precio_actual),
            "arbol_precio": self.por_precio.metricas(),
            "arbol_tiempo": self.por_tiempo.metricas(),
        }