"""Etapa 0 — Ingesta y buffer (fila B del plan — todos).

Estructura: cola FIFO propia sobre lista enlazada, con capacidad acotada.

También genera el componente sintético del escenario B que el CSV real no trae
(órdenes, tipo de envío, tarjetas, duplicados y ráfagas de fraude). Todo lo
aleatorio sale de SEMILLA: misma semilla, mismos datos.
"""
from __future__ import annotations

import csv
import heapq
import random
from collections import deque
from collections.abc import Iterable, Iterator
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .evento import Event

SEMILLA = 42

# Tamaños de los experimentos: se leen con leer_csv(ruta, limite=TAMANOS[...]).
TAMANOS = {
    "1K": 1_000,
    "10K": 10_000,
    "100K": 100_000,
    "1M": 1_000_000,
    "10M": 10_000_000,
}

# --- Parámetros del componente sintético ---
PROPORCION_ENVIO = {"express": 0.2, "estandar": 0.6, "programada": 0.2}
MAX_TARJETAS_POR_USUARIO = 2
TASA_DUP = 0.02  # fracción de eventos que se reenvían
DISTANCIA_MEDIA_DUP = 20_000  # eventos entre el original y su copia (distribución exponencial)
TASA_RAFAGA = 0.002  # probabilidad de que una compra real dispare una ráfaga de fraude
INTENTOS_POR_RAFAGA = 10  # uno por segundo; supera el umbral de la etapa 6 (5 por ventana de 300 s)
N_TARJETAS_ROBADAS = 100
FRACCION_SENALADAS = 0.5  # de las tarjetas robadas, cuántas se conocen de antemano
USUARIO_FRAUDE_BASE = 10**10  # ids de las cuentas del atacante, fuera del rango real

_CAMPOS_REALES = (
    "event_time", "event_type", "product_id", "category_id", "category_code",
    "brand", "price", "user_id", "user_session",
)


def _a_fecha(texto: str) -> datetime:
    """'2019-10-01 00:00:00 UTC' -> datetime en UTC."""
    return datetime.fromisoformat(texto[:19]).replace(tzinfo=timezone.utc)


def leer_csv(
    ruta: Path | str, limite: int | None = None, stats: dict[str, int] | None = None
) -> Iterator[Event]:
    """Lee el CSV real de forma perezosa y entrega Event con los tipos del contrato.

    - Las columnas se ubican por el encabezado.
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
                emitidos += 1
                yield ev
    finally:
        if stats is not None:
            stats["leidas"] = leidas
            stats["invalidas"] = invalidas


class Sintetizador:
    """Agrega al stream real los campos y eventos sintéticos del escenario B.

    Campos, solo en las compras:
      - order_id: derivado, = user_session (una orden son las compras de una sesión).
      - tipo_envio: se sortea una vez por orden según PROPORCION_ENVIO.
      - card_id: cada usuario tiene entre 1 y MAX_TARJETAS_POR_USUARIO tarjetas fijas.
    Eventos agregados al stream:
      - Duplicados (is_dup=True): con probabilidad TASA_DUP un evento se reenvía más
        adelante, a una distancia exponencial de media DISTANCIA_MEDIA_DUP eventos.
        Los duplicados exactos que ya trae el CSV también se marcan.
      - Fraude (is_fraud=True): con probabilidad TASA_RAFAGA una compra dispara una
        ráfaga de INTENTOS_POR_RAFAGA intentos, uno por segundo, con una tarjeta robada.
        Solo una parte de las tarjetas robadas está señalada de antemano (`senaladas`).
    """

    def __init__(self, seed: int = SEMILLA) -> None:
        self._rng = random.Random(seed)
        self.tarjetas_robadas = [f"R{i:03d}" for i in range(N_TARJETAS_ROBADAS)]
        rng_senaladas = random.Random(f"{seed}-senaladas")  # no depende de cuánto se lea
        self.senaladas = sorted(
            rng_senaladas.sample(self.tarjetas_robadas, int(N_TARJETAS_ROBADAS * FRACCION_SENALADAS))
        )
        self._envio_por_orden: dict[str, str] = {}
        self._tarjetas_por_usuario: dict[int, list[str]] = {}
        self.duplicados_reales = 0
        self.duplicados_inyectados = 0
        self.rafagas = 0
        self.intentos_fraude = 0

    def flujo(self, eventos: Iterable[Event]) -> Iterator[Event]:
        """Entrega los eventos reales enriquecidos, intercalando duplicados e intentos de fraude."""
        rng = self._rng
        pendientes_dup: list[tuple[int, int, Event]] = []  # (posición de salida, orden, copia)
        pendientes_fraude: list[tuple[datetime, int, Event]] = []  # (hora, orden, intento)
        compras_recientes: deque[Event] = deque(maxlen=1_000)  # productos para las ráfagas
        filas_recientes: deque[tuple] = deque()  # para marcar los duplicados que ya trae el CSV
        filas_recientes_set: set[tuple] = set()
        posicion = orden = 0

        for ev in eventos:
            # Primero sale lo que ya "llegó": intentos con hora <= la de este evento y copias atrasadas.
            while pendientes_fraude and pendientes_fraude[0][0] <= ev.event_time:
                yield heapq.heappop(pendientes_fraude)[2]
                posicion += 1
            while pendientes_dup and pendientes_dup[0][0] <= posicion:
                yield heapq.heappop(pendientes_dup)[2]
                posicion += 1

            self._marcar_duplicado_real(ev, filas_recientes, filas_recientes_set)
            self._enriquecer(ev)
            if ev.event_type == "purchase":
                compras_recientes.append(ev)
                if rng.random() < TASA_RAFAGA:
                    for intento in self._rafaga(ev, compras_recientes):
                        orden += 1
                        heapq.heappush(pendientes_fraude, (intento.event_time, orden, intento))
            if rng.random() < TASA_DUP:
                distancia = 1 + int(rng.expovariate(1 / DISTANCIA_MEDIA_DUP))
                orden += 1
                heapq.heappush(pendientes_dup, (posicion + distancia, orden, replace(ev, is_dup=True)))
                self.duplicados_inyectados += 1

            yield ev
            posicion += 1

        for pendientes in (pendientes_fraude, pendientes_dup):  # lo que quedó al agotarse la fuente
            while pendientes:
                yield heapq.heappop(pendientes)[2]

    def _marcar_duplicado_real(self, ev: Event, recientes: deque[tuple], recientes_set: set[tuple]) -> None:
        # En el CSV real las copias aparecen a 60 filas como máximo: alcanza con recordar 1.000.
        fila = (ev.event_time, ev.event_type, ev.product_id, ev.category_id, ev.category_code,
                ev.brand, ev.price, ev.user_id, ev.user_session)
        if fila in recientes_set:
            ev.is_dup = True
            self.duplicados_reales += 1
            return
        recientes.append(fila)
        recientes_set.add(fila)
        if len(recientes) > 1_000:
            recientes_set.discard(recientes.popleft())

    def _enriquecer(self, ev: Event) -> None:
        if ev.event_type != "purchase":
            return
        ev.order_id = ev.user_session
        if ev.order_id is None:
            ev.tipo_envio = self._sortear_envio()
        else:  # todas las compras de una orden comparten el envío
            if ev.order_id not in self._envio_por_orden:
                self._envio_por_orden[ev.order_id] = self._sortear_envio()
            ev.tipo_envio = self._envio_por_orden[ev.order_id]
        tarjetas = self._tarjetas_por_usuario.get(ev.user_id)
        if tarjetas is None:
            n = self._rng.randint(1, MAX_TARJETAS_POR_USUARIO)
            tarjetas = self._tarjetas_por_usuario[ev.user_id] = [f"T{ev.user_id}-{k}" for k in range(n)]
        ev.card_id = tarjetas[0] if len(tarjetas) == 1 else self._rng.choice(tarjetas)

    def _sortear_envio(self) -> str:
        return self._rng.choices(list(PROPORCION_ENVIO), weights=list(PROPORCION_ENVIO.values()))[0]

    def _rafaga(self, disparador: Event, compras_recientes: deque[Event]) -> Iterator[Event]:
        """Intentos de compra con una tarjeta robada desde una cuenta del atacante."""
        rng = self._rng
        self.rafagas += 1
        tarjeta = rng.choice(self.tarjetas_robadas)
        cuenta = USUARIO_FRAUDE_BASE + self.rafagas
        sesion = f"fraude-{self.rafagas}"
        envio = self._sortear_envio()
        # Un intento por segundo: dos intentos iguales en el mismo segundo serían un duplicado para la etapa 1.
        for segundo in range(INTENTOS_POR_RAFAGA):
            base = rng.choice(compras_recientes)  # un producto real comprado hace poco
            self.intentos_fraude += 1
            yield Event(
                event_time=disparador.event_time + timedelta(seconds=segundo),
                event_type="purchase",
                product_id=base.product_id,
                category_id=base.category_id,
                category_code=base.category_code,
                brand=base.brand,
                price=base.price,
                user_id=cuenta,
                user_session=sesion,
                order_id=sesion,
                tipo_envio=envio,
                card_id=tarjeta,
                is_fraud=True,
            )

    def metricas(self) -> dict[str, Any]:
        return {
            "duplicados_reales": self.duplicados_reales,
            "duplicados_inyectados": self.duplicados_inyectados,
            "rafagas_fraude": self.rafagas,
            "intentos_fraude": self.intentos_fraude,
            "tarjetas_senaladas": len(self.senaladas),
        }


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
    """Agrega el componente sintético y pasa el stream por el buffer FIFO en lotes.

    El productor (la fuente) encola hasta juntar `tam_lote` eventos y el
    consumidor (el pipeline) los saca de una vez. Si el buffer se llena antes
    (capacidad < tam_lote), hay backpressure: el productor no puede encolar, se
    entrega lo acumulado y recién entonces sigue.

    `sintetizar=False` deja pasar la fuente tal cual (útil para probar el buffer solo).
    """

    nombre = "etapa0_ingesta"

    def __init__(self, capacidad: int, tam_lote: int, sintetizar: bool = True) -> None:
        if tam_lote < 1:
            raise ValueError("El tamaño de lote debe ser al menos 1.")
        self.buffer = ColaFIFO(capacidad)
        self.tam_lote = tam_lote
        self.sintetizador = Sintetizador() if sintetizar else None
        self.ingeridos = 0
        self.lotes_emitidos = 0
        self.bloqueos = 0  # veces que el productor encontró el buffer lleno
        self.ocupacion_max = 0

    def senalados(self) -> list[str]:
        """Tarjetas señaladas de antemano: la etapa 6 las carga en su Bloom Filter."""
        return list(self.sintetizador.senaladas) if self.sintetizador else []

    def lotes(self, fuente: Iterable[Event]) -> Iterator[list[Event]]:
        """Pasa la fuente por el buffer y entrega lotes de hasta `tam_lote` eventos."""
        if self.sintetizador is not None:
            fuente = self.sintetizador.flujo(fuente)
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
        metricas = {
            "ingeridos": self.ingeridos,
            "lotes": self.lotes_emitidos,
            "ocupacion_max": self.ocupacion_max,
            "bloqueos": self.bloqueos,
        }
        if self.sintetizador is not None:
            metricas["sintetico"] = self.sintetizador.metricas()
        return metricas
