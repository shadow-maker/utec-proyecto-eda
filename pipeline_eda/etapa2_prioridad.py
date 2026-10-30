"""Etapa 2 — Cola con prioridades.

Heap binario de mínimos: alertas, luego express, estándar, programada y navegación.
"""
from __future__ import annotations

from typing import Any

from .evento import Alerta, Event, Prioridad


class HeapMin:
    """Heap binario de mínimos sobre lista. push/pop O(log n).

    Los hijos del nodo i están en 2i+1 y 2i+2; su padre, en (i-1)//2.
    Los elementos se guardan como (prioridad, secuencia, item): la secuencia
    mantiene el orden de llegada entre elementos de igual prioridad y, como
    nunca se repite, Python nunca llega a comparar los items.
    """

    def __init__(self) -> None:
        self._datos: list[tuple[int, int, Any]] = []

    def push(self, prioridad: int, secuencia: int, item: Any) -> None:
        """Agrega al final y sube el elemento mientras sea menor que su padre."""
        datos = self._datos
        datos.append((prioridad, secuencia, item))
        i = len(datos) - 1
        while i > 0:
            padre = (i - 1) // 2
            if not datos[i] < datos[padre]:
                break
            datos[i], datos[padre] = datos[padre], datos[i]
            i = padre

    def pop(self) -> Any:
        """Saca el mínimo: pone el último en la raíz y lo baja. IndexError si está vacío."""
        datos = self._datos
        ultimo = datos.pop()
        if not datos:  # era el único elemento
            return ultimo[2]
        raiz = datos[0]
        datos[0] = ultimo
        self._bajar(0)
        return raiz[2]

    def _bajar(self, i: int) -> None:
        """Baja el elemento de la posición i mientras sea mayor que su hijo menor."""
        datos = self._datos
        n = len(datos)
        while True:
            menor = i
            izquierdo, derecho = 2 * i + 1, 2 * i + 2
            if izquierdo < n and datos[izquierdo] < datos[menor]:
                menor = izquierdo
            if derecho < n and datos[derecho] < datos[menor]:
                menor = derecho
            if menor == i:
                return
            datos[i], datos[menor] = datos[menor], datos[i]
            i = menor

    def __len__(self) -> int:
        return len(self._datos)


_PRIORIDAD_ENVIO = {
    "express": Prioridad.EXPRESS,
    "estandar": Prioridad.ESTANDAR,
    "programada": Prioridad.PROGRAMADA,
}


def prioridad_de(ev: Event) -> Prioridad:
    """Prioridad según el tipo de evento y el tipo de envío."""
    if ev.event_type != "purchase":  # view / cart: no hay orden que despachar
        return Prioridad.NAVEGACION
    return _PRIORIDAD_ENVIO.get(ev.tipo_envio, Prioridad.ESTANDAR)


class ColaPrioridad:
    nombre = "etapa2_prioridad"

    def __init__(self) -> None:
        self._heap = HeapMin()
        self._secuencia = 0
        self.encolados = {p.name: 0 for p in Prioridad}
        self.tamano_max = 0

    def _push(self, prioridad: Prioridad, item: Event | Alerta) -> None:
        self._secuencia += 1
        self._heap.push(int(prioridad), self._secuencia, item)
        self.encolados[prioridad.name] += 1
        self.tamano_max = max(self.tamano_max, len(self._heap))

    def push_evento(self, ev: Event) -> None:
        self._push(prioridad_de(ev), ev)

    def push_alerta(self, alerta: Alerta) -> None:
        self._push(Prioridad.ALERTA, alerta)

    def pop(self) -> Event | Alerta:
        return self._heap.pop()

    def __len__(self) -> int:
        return len(self._heap)

    def metricas(self) -> dict[str, Any]:
        """Elementos encolados por prioridad y tamaño máximo del heap."""
        return {"encolados_por_prioridad": dict(self.encolados), "tamano_max": self.tamano_max}
