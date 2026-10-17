"""Etapa 0 — Ingesta y buffer (fila B del plan — todos).

Estructura: cola FIFO propia sobre lista enlazada, con capacidad acotada.
"""
from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .evento import Event


def leer_csv(ruta: Path | str, limite: int | None = None) -> Iterator[Event]:
    """Lee el CSV enriquecido de forma perezosa (csv.reader) y entrega Event."""

    with open(ruta, mode="r") as file:
        reader = csv.reader(file)

        keys = next(reader)

        for line in reader:
            try:
                event = Event(
                    event_time=line[0],
                    event_type=line[1],
                    product_id=int(line[2]),
                    category_id=int(line[3]),
                    category_code=line[4],
                    brand=line[5],
                    price=float(line[6]),
                    user_id=int(line[7]),
                    user_session=line[8]
                )
            except ValueError as e:
                print(f"Error al convertir fila: {line}. Error: {e}")
                continue

            yield event

class _Nodo:
    __slots__ = ("valor", "siguiente")

    def __init__(self, valor: Any) -> None:
        self.valor = valor
        self.siguiente: _Nodo | None = None


class ColaFIFO:
    """Cola FIFO acotada sobre lista enlazada simple. encolar/desencolar O(1)."""

    def __init__(self, capacidad: int | None = None) -> None:
        self.capacidad = capacidad
        self._cabeza: _Nodo | None = None
        self._cola: _Nodo | None = None
        self._tamano = 0

    def encolar(self, item: Any) -> bool:
        """Devuelve False si el buffer está lleno (backpressure)."""
        raise NotImplementedError

    def desencolar(self) -> Any:
        raise NotImplementedError

    def desencolar_lote(self, k: int) -> list[Any]:
        raise NotImplementedError

    def __len__(self) -> int:
        return self._tamano


class Ingesta:
    nombre = "etapa0_ingesta"

    def __init__(self, capacidad: int, tam_lote: int) -> None:
        self.buffer = ColaFIFO(capacidad)
        self.tam_lote = tam_lote

    def lotes(self, fuente: Iterable[Event]) -> Iterator[list[Event]]:
        """Pasa la fuente por el buffer y entrega lotes de hasta `tam_lote` eventos."""
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Eventos ingeridos, ocupación máxima del buffer, bloqueos, throughput."""
        raise NotImplementedError
