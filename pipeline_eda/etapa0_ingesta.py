"""Etapa 0 — Ingesta y buffer (fila B del plan — todos).

Estructura: cola FIFO propia sobre lista enlazada, con capacidad acotada.
"""
from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evento import Event

_CAMPOS_REALES = (
    "event_time", "event_type", "product_id", "category_id", "category_code",
    "brand", "price", "user_id", "user_session",
)
_CAMPOS_SINTETICOS = ("order_id", "tipo_envio", "card_id", "device_id")  # opcionales
_CAMPOS_VERDAD = ("is_fraud", "is_dup")  # opcionales
_VERDADERO = frozenset({"1", "True", "true"})


def _a_fecha(texto: str) -> datetime:
    """'2019-10-01 00:00:00 UTC' (o segundos desde 1970, si viene numérico) -> datetime en UTC."""
    if texto.isdigit():
        return datetime.fromtimestamp(int(texto), timezone.utc)
    return datetime.fromisoformat(texto[:19]).replace(tzinfo=timezone.utc)


def leer_csv(
    ruta: Path | str, limite: int | None = None, stats: dict[str, int] | None = None
) -> Iterator[Event]:
    """Lee el CSV (real o enriquecido) de forma perezosa y entrega Event con los tipos del contrato.

    - Las columnas se ubican por el encabezado; las sintéticas y las de verdad son opcionales.
    - event_time pasa a datetime (UTC), los números a int/float y el texto vacío a None.
    - Una fila con otro número de columnas o que no se puede convertir se descarta y se cuenta.
    - `limite`: como máximo esa cantidad de eventos. `stats` recibe "leidas" e "invalidas" al terminar.

    La validación semántica (precio > 0, tipo de evento conocido...) es de la etapa 1.
    """
    leidas = invalidas = emitidos = 0
    ultimo_texto, ultima_fecha = None, None
    try:
        with open(ruta, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            encabezado = next(reader, None)
            if encabezado is None:
                return
            col = {nombre: i for i, nombre in enumerate(encabezado)}
            faltan = [c for c in _CAMPOS_REALES if c not in col]
            if faltan:
                raise ValueError(f"Faltan columnas en {ruta}: {faltan}")
            i_time, i_type, i_prod, i_cat, i_code, i_brand, i_price, i_user, i_ses = (
                col[c] for c in _CAMPOS_REALES
            )
            sinteticos = [(c, col[c]) for c in _CAMPOS_SINTETICOS if c in col]
            verdad = [(c, col[c]) for c in _CAMPOS_VERDAD if c in col]
            n_columnas = len(encabezado)

            for fila in reader:
                if limite is not None and emitidos >= limite:
                    break
                leidas += 1
                if len(fila) != n_columnas:
                    invalidas += 1
                    continue
                try:
                    texto = fila[i_time]
                    if texto != ultimo_texto:  # el CSV viene ordenado: muchas filas comparten segundo
                        ultima_fecha = _a_fecha(texto)
                        ultimo_texto = texto
                    ev = Event(
                        event_time=ultima_fecha,
                        event_type=fila[i_type],
                        product_id=int(fila[i_prod]),
                        category_id=int(fila[i_cat]),
                        category_code=fila[i_code] or None,
                        brand=fila[i_brand] or None,
                        price=float(fila[i_price]),
                        user_id=int(fila[i_user]),
                        user_session=fila[i_ses] or None,
                    )
                except ValueError:
                    invalidas += 1
                    continue
                for nombre, i in sinteticos:
                    setattr(ev, nombre, fila[i] or None)
                for nombre, i in verdad:
                    setattr(ev, nombre, fila[i] in _VERDADERO)
                emitidos += 1
                yield ev
    finally:
        if stats is not None:
            stats["leidas"] = leidas
            stats["invalidas"] = invalidas


class _Nodo:
    __slots__ = ("valor", "siguiente")

    def __init__(self, valor: Any) -> None:
        self.valor = valor
        self.siguiente: _Nodo | None = None


class ColaFIFO:
    """Cola FIFO acotada sobre lista enlazada simple. encolar/desencolar O(1)."""

    def __init__(self, capacidad: int | None = None) -> None:
        if capacidad is not None and capacidad < 1:
            raise ValueError("La capacidad debe ser al menos 1 (o None para no acotarla).")
        self.capacidad = capacidad
        self._cabeza: _Nodo | None = None  # de aquí se desencola (el más antiguo)
        self._cola: _Nodo | None = None  # aquí se encola (el más reciente)
        self._tamano = 0

    def encolar(self, item: Any) -> bool:
        """Agrega al final. Devuelve False si el buffer está lleno (backpressure)."""
        if self.capacidad is not None and self._tamano >= self.capacidad:
            return False
        nodo = _Nodo(item)
        if self._cola is None:  # cola vacía: el nodo es cabeza y cola a la vez
            self._cabeza = nodo
        else:
            self._cola.siguiente = nodo
        self._cola = nodo
        self._tamano += 1
        return True

    def desencolar(self) -> Any:
        """Saca el elemento más antiguo. IndexError si la cola está vacía (como deque)."""
        if self._cabeza is None:
            raise IndexError("desencolar de una cola vacía")
        nodo = self._cabeza
        self._cabeza = nodo.siguiente
        if self._cabeza is None:
            self._cola = None
        self._tamano -= 1
        return nodo.valor

    def desencolar_lote(self, k: int) -> list[Any]:
        """Saca hasta k elementos en orden de llegada. O(k)."""
        lote = []
        nodo = self._cabeza
        while nodo is not None and len(lote) < k:
            lote.append(nodo.valor)
            nodo = nodo.siguiente
        self._cabeza = nodo
        if nodo is None:
            self._cola = None
        self._tamano -= len(lote)
        return lote

    def __len__(self) -> int:
        return self._tamano


class Ingesta:
    """Pasa el stream por el buffer FIFO y lo entrega en lotes a la etapa 1.

    El productor (la fuente) encola hasta juntar `tam_lote` eventos y el
    consumidor (el pipeline) los saca de una vez. Si el buffer se llena antes
    (capacidad < tam_lote), hay backpressure: el productor no puede encolar, se
    entrega lo acumulado y recién entonces sigue.
    """

    nombre = "etapa0_ingesta"

    def __init__(self, capacidad: int, tam_lote: int) -> None:
        if tam_lote < 1:
            raise ValueError("El tamaño de lote debe ser al menos 1.")
        self.buffer = ColaFIFO(capacidad)
        self.tam_lote = tam_lote
        self.ingeridos = 0
        self.lotes_emitidos = 0
        self.bloqueos = 0  # veces que el productor encontró el buffer lleno
        self.ocupacion_max = 0

    def lotes(self, fuente: Iterable[Event]) -> Iterator[list[Event]]:
        """Pasa la fuente por el buffer y entrega lotes de hasta `tam_lote` eventos."""
        for ev in fuente:
            if not self.buffer.encolar(ev):  # lleno: se drena antes de seguir
                self.bloqueos += 1
                yield self._sacar_lote()
                self.buffer.encolar(ev)  # el buffer quedó vacío: ahora sí entra
            if len(self.buffer) >= self.tam_lote:
                yield self._sacar_lote()
        while len(self.buffer):  # lo que quedó al agotarse la fuente
            yield self._sacar_lote()

    def _sacar_lote(self) -> list[Event]:
        self.ocupacion_max = max(self.ocupacion_max, len(self.buffer))
        lote = self.buffer.desencolar_lote(self.tam_lote)
        self.ingeridos += len(lote)
        self.lotes_emitidos += 1
        return lote

    def metricas(self) -> dict[str, Any]:
        """Eventos ingeridos, lotes, ocupación máxima del buffer y bloqueos."""
        return {
            "ingeridos": self.ingeridos,
            "lotes": self.lotes_emitidos,
            "ocupacion_max": self.ocupacion_max,
            "bloqueos": self.bloqueos,
        }
