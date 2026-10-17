"""Etapa 2 — Cola con prioridades (responsable: A).

Estructura: heap binario de mínimos propio. Express > estándar > programada;
las alertas de la etapa 6 se atienden antes que todo.
"""
from __future__ import annotations

from typing import Any

from .evento import Alerta, Event, Prioridad


class HeapMin:
    """Heap binario de mínimos sobre lista. push/pop O(log n).

    Los elementos se guardan como (prioridad, secuencia, item): la secuencia
    mantiene el orden de llegada entre elementos de igual prioridad.
    """

    def __init__(self) -> None:
        self._datos: list[tuple[int, int, Any]] = []

    def push(self, prioridad: int, secuencia: int, item: Any) -> None:
        raise NotImplementedError

    def pop(self) -> Any:
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self._datos)


def prioridad_de(ev: Event) -> Prioridad:
    """Prioridad según el tipo de evento y el tipo de envío."""
    raise NotImplementedError


class ColaPrioridad:
    nombre = "etapa2_prioridad"

    def __init__(self) -> None:
        self._heap = HeapMin()
        self._secuencia = 0

    def push_evento(self, ev: Event) -> None:
        raise NotImplementedError

    def push_alerta(self, alerta: Alerta) -> None:
        raise NotImplementedError

    def pop(self) -> Event | Alerta:
        raise NotImplementedError

    def __len__(self) -> int:
        return len(self._heap)

    def metricas(self) -> dict[str, Any]:
        """Atendidos por prioridad, tamaño máximo del heap, espera promedio."""
        raise NotImplementedError
