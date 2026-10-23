"""Etapa 1 — Preprocesamiento por lotes (responsable: A).

Estructuras: ordenación eficiente propia + búsqueda binaria para limpiar y
deduplicar.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .evento import Event


def merge_sort(items: list[Any], clave: Callable[[Any], Any]) -> list[Any]:
    """Merge sort natural, iterativo y estable. Devuelve una lista nueva.

    1. Calcula la clave una sola vez por elemento (n llamadas, no n log n).
    2. Parte la entrada en tramos ya ordenados: un lote que llega ordenado por
       tiempo es un único tramo y cuesta O(n).
    3. Mezcla los tramos de a pares, alternando entre dos buffers de índices,
       hasta que queda uno solo. Peor caso O(n log n) tiempo, O(n) espacio extra.

    Solo se comparan claves, nunca los elementos: dos Event no son comparables.
    Estable: entre claves iguales se conserva el orden de llegada.
    """
    n = len(items)
    if n < 2:
        return list(items)
    claves = [clave(x) for x in items]

    # Inicio de cada tramo no decreciente; el corte es estricto (<) para que
    # las claves iguales queden en el mismo tramo y se mantenga la estabilidad.
    limites = [0]
    for i in range(1, n):
        if claves[i] < claves[i - 1]:
            limites.append(i)
    limites.append(n)

    origen = list(range(n))
    destino = [0] * n
    while len(limites) > 2:
        nuevos = [0]
        for j in range(0, len(limites) - 1, 2):
            ini = limites[j]
            if j + 2 < len(limites):
                medio = limites[j + 1]
                fin = limites[j + 2]
                _merge(claves, origen, destino, ini, medio, fin)
            else:  # tramo sin pareja: pasa tal cual a la siguiente ronda
                fin = limites[j + 1]
                destino[ini:fin] = origen[ini:fin]
            nuevos.append(fin)
        origen, destino = destino, origen
        limites = nuevos
    return [items[i] for i in origen]


def _merge(
    claves: list[Any], origen: list[int], destino: list[int], ini: int, medio: int, fin: int
) -> None:
    """Mezcla origen[ini:medio] y origen[medio:fin] (índices ordenados por clave) en destino[ini:fin]."""
    # `destino` llega por object reference: es la misma lista que tiene merge_sort,
    # así que escribir destino[k] o destino[k:fin] la modifica allá, sin devolver
    # nada. Se reutiliza un solo buffer de tamaño n en vez de crear listas por merge.
    if not claves[origen[medio]] < claves[origen[medio - 1]]:  # ya están en orden
        destino[ini:fin] = origen[ini:fin]
        return
    i, j, k = ini, medio, ini
    while i < medio and j < fin:
        # Se toma de la derecha solo si es estrictamente menor: así es estable.
        if claves[origen[j]] < claves[origen[i]]:
            destino[k] = origen[j]
            j += 1
        else:
            destino[k] = origen[i]
            i += 1
        k += 1
    if i < medio:
        destino[k:fin] = origen[i:medio]
    else:
        destino[k:fin] = origen[j:fin]


def busqueda_binaria(ordenados: list[Any], objetivo: Any) -> int:
    """Índice de `objetivo` en `ordenados`, o -1 si no está. O(log n).

    Si `objetivo` aparece varias veces, devuelve la primera aparición.
    """
    lo = 0
    hi = len(ordenados)

    # Primera posición i con ordenados[i] >= objetivo (len si no hay). Equivale a bisect_left.
    while lo < hi:  # invariante: ordenados[:lo] < objetivo <= ordenados[hi:]
        medio = (lo + hi) // 2
        if ordenados[medio] < objetivo:
            lo = medio + 1
        else:
            hi = medio

    if lo < len(ordenados) and ordenados[lo] == objetivo: # validacion extra
        return lo
    return -1


def _merge_listas(a: list[Any], b: list[Any]) -> list[Any]:
    """Mezcla dos listas ordenadas en una lista nueva. O(len(a) + len(b)).

    Es el mismo merge de merge_sort, pero sobre valores y devolviendo el resultado:
    aquí no hay un buffer que reutilizar, porque la ventana cambia de tamaño.
    """
    resultado = []
    i, j = 0, 0
    while i < len(a) and j < len(b):
        if b[j] < a[i]:
            resultado.append(b[j])
            j += 1
        else:
            resultado.append(a[i])
            i += 1
    resultado.extend(a[i:])
    resultado.extend(b[j:])
    return resultado


TIPOS_EVENTO = frozenset({"view", "cart", "purchase"})


class Preprocesador:
    """Limpia y deduplica cada lote de la etapa 0.

    Ventana de deduplicación: lista ordenada con las claves de los últimos
    `ventana_dedup` eventos emitidos. Como la clave empieza por event_time, el
    orden por clave es también orden temporal: las claves más viejas están al
    principio y vencerlas es borrar un prefijo.
    """

    nombre = "etapa1_preproceso"

    def __init__(self, ventana_dedup: int = 100_000) -> None:
        self.ventana_dedup = ventana_dedup  # cuántas claves recientes se recuerdan entre lotes
        self._claves_vistas: list[tuple] = []  # ordenadas, para búsqueda binaria
        self.recibidos = 0
        self.invalidos: dict[str, int] = {}  # motivo -> cantidad
        self.duplicados_lote = 0
        self.duplicados_ventana = 0
        self.emitidos = 0

    @staticmethod
    def clave(ev: Event) -> tuple:
        """Clave que identifica un evento repetido.

        event_time va primero para que ordenar por clave sea ordenar por tiempo.
        `or ""` evita comparar None con str si dos claves empatan hasta la sesión.
        """
        return (ev.event_time, ev.event_type, ev.product_id, ev.user_id, ev.user_session or "")

    def procesar(self, lote: list[Event]) -> list[Event]:
        """validar → normalizar → ordenar por clave → descartar duplicados.

        Devuelve los eventos que sobreviven, en orden de clave (= temporal).
        Entre copias de un mismo evento se conserva la primera que llegó.
        O(B log B + B log W + W) por lote; O(B log W) si el lote ya viene ordenado.
        """
        self.recibidos += len(lote)

        validos = []
        for ev in lote:
            motivo = self._motivo_invalido(ev)
            if motivo is None:
                validos.append(self._normalizar(ev))
            else:
                self.invalidos[motivo] = self.invalidos.get(motivo, 0) + 1

        # Se ordenan índices para calcular cada clave una sola vez y reutilizarla abajo.
        claves = [self.clave(ev) for ev in validos]
        orden = merge_sort(list(range(len(validos))), claves.__getitem__)

        salida = []
        nuevas = []  # claves emitidas en este lote; salen ordenadas
        anterior = None
        for i in orden:
            k = claves[i]
            if k == anterior:  # ordenado, una copia queda junto a la anterior
                self.duplicados_lote += 1
                continue
            anterior = k
            if busqueda_binaria(self._claves_vistas, k) != -1:
                self.duplicados_ventana += 1
                continue
            nuevas.append(k)
            salida.append(validos[i])

        self._actualizar_ventana(nuevas)
        self.emitidos += len(salida)
        return salida

    def _actualizar_ventana(self, nuevas: list[tuple]) -> None:
        """Agrega las claves del lote y se queda con las `ventana_dedup` más recientes."""
        if not nuevas:
            return
        vistas = self._claves_vistas
        if not vistas or vistas[-1] < nuevas[0]:
            # Caso normal: el stream viene ordenado por tiempo y todo lo nuevo es
            # posterior a la ventana, así que basta pegarlo al final.
            vistas.extend(nuevas)
        else:  # llegaron eventos atrasados: hay que intercalarlos
            vistas = self._claves_vistas = _merge_listas(vistas, nuevas)
        exceso = len(vistas) - self.ventana_dedup
        if exceso > 0:
            del vistas[:exceso]  # las más viejas están al principio

    def _motivo_invalido(self, ev: Event) -> str | None:
        """Motivo por el que se descarta el evento, o None si es válido."""
        if ev.event_type not in TIPOS_EVENTO:
            return "tipo_evento"
        if ev.product_id <= 0 or ev.category_id <= 0 or ev.user_id <= 0:
            return "id"
        if not ev.user_session:
            return "sin_sesion"
        if not ev.price > 0:  # precio 0 = dato faltante; `not >` también descarta NaN
            return "precio"
        return None

    def _normalizar(self, ev: Event) -> Event:
        """Modifica el evento en el lugar: texto vacío -> None, minúsculas, precio a 2 decimales."""
        if ev.category_code is not None:
            ev.category_code = ev.category_code.strip().lower() or None
        if ev.brand is not None:
            ev.brand = ev.brand.strip().lower() or None
        ev.price = round(ev.price, 2)
        return ev

    def metricas(self) -> dict[str, Any]:
        """Eventos recibidos, inválidos y duplicados descartados."""
        return {
            "recibidos": self.recibidos,
            "invalidos": sum(self.invalidos.values()),
            "invalidos_por_motivo": dict(self.invalidos),
            "duplicados_lote": self.duplicados_lote,
            "duplicados_ventana": self.duplicados_ventana,
            "emitidos": self.emitidos,
            "tamano_ventana": len(self._claves_vistas),
        }
