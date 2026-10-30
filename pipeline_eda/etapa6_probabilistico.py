"""Etapa 6 [FIJA] — Filtrado probabilístico.

Estructuras: Bloom Filter para tarjetas señaladas y Count-Min Sketch para la
intensidad de intentos de compra por tarjeta en una ventana temporal.
Un positivo del Bloom Filter se verifica contra el conjunto exacto antes de
bloquear la operación. Las alertas de intensidad se confirman sin verificar:
con los parámetros del sketch, la sobreestimación esperada es menor que 1 intento.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable
from typing import Any

from .evento import Alerta, Event


def dos_hashes(clave: str, semilla: int = 0) -> tuple[int, int]:
    """Un solo hash de 128 bits partido en dos enteros de 64 (doble hashing de Kirsch–Mitzenmacher).

    La función i se obtiene como h1 + i·h2. h2 es impar para que nunca valga 0
    (si no, todas las funciones darían la misma posición).
    """
    d = hashlib.blake2b(f"{semilla}:{clave}".encode(), digest_size=16).digest()
    return int.from_bytes(d[:8], "little"), int.from_bytes(d[8:], "little") | 1


class BloomFilter:
    """m bits y k funciones hash, calculados a partir de n esperado y tasa de FP.

    agregar y __contains__ son O(k); el espacio es O(m) bits.
    """

    def __init__(self, n_esperado: int, tasa_fp: float) -> None:
        self.m = math.ceil(-n_esperado * math.log(tasa_fp) / math.log(2) ** 2)
        self.k = max(1, round(self.m / n_esperado * math.log(2)))
        self.bits = bytearray(math.ceil(self.m / 8))  # el bit pos está en el byte pos // 8

    def agregar(self, clave: str) -> None:
        h1, h2 = dos_hashes(clave)
        for i in range(self.k):
            pos = (h1 + i * h2) % self.m
            self.bits[pos // 8] |= 1 << (pos % 8)

    def __contains__(self, clave: str) -> bool:
        """False: seguro que no se agregó. True: posiblemente se agregó."""
        h1, h2 = dos_hashes(clave)
        for i in range(self.k):
            pos = (h1 + i * h2) % self.m
            if not self.bits[pos // 8] >> (pos % 8) & 1:
                return False
        return True


class CountMinSketch:
    """Matriz profundidad × ancho de contadores. Puede sobreestimar, nunca subestimar.

    Con ancho w y profundidad d: estimado <= real + (e/w)·total con probabilidad >= 1 - e^(-d).
    agregar y estimar son O(d); el espacio es O(w·d).
    """

    def __init__(self, ancho: int, profundidad: int, seed: int = 0) -> None:
        self.ancho = ancho
        self.profundidad = profundidad
        self.seed = seed
        self.tabla = [[0] * ancho for _ in range(profundidad)]
        self.total = 0

    def agregar(self, clave: str, cantidad: int = 1) -> None:
        """Suma en una casilla de cada fila; la fila j usa la función hash h1 + j·h2."""
        h1, h2 = dos_hashes(clave, self.seed)
        for j in range(self.profundidad):
            self.tabla[j][(h1 + j * h2) % self.ancho] += cantidad
        self.total += cantidad

    def estimar(self, clave: str) -> int:
        """Mínimo entre las filas: la casilla con menos colisiones de otras claves."""
        h1, h2 = dos_hashes(clave, self.seed)
        return min(self.tabla[j][(h1 + j * h2) % self.ancho] for j in range(self.profundidad))

    def reiniciar(self) -> None:
        """Vacía los contadores al empezar una nueva ventana. O(w·d)."""
        self.tabla = [[0] * self.ancho for _ in range(self.profundidad)]
        self.total = 0


class DetectorFraude:
    nombre = "etapa6_probabilistico"

    def __init__(
        self,
        ventana_seg: int = 300,
        umbral: int = 5,
        tasa_fp: float = 0.01,
        ancho_cms: int = 2_000,
        profundidad_cms: int = 5,
        seed: int = 42,
    ) -> None:
        self.ventana_seg = ventana_seg
        self.umbral = umbral
        self.tasa_fp = tasa_fp
        self.senalados: BloomFilter | None = None  # se dimensiona en cargar_senalados()
        self.senalados_exacto: set[str] = set()  # solo para verificar positivos
        self.intensidad = CountMinSketch(ancho_cms, profundidad_cms, seed)
        self.inicio_ventana = None
        self.ventanas = 0
        self.alertas = {"senalada": 0, "intensidad": 0}
        self.confirmadas = 0
        self.falsos_positivos = 0

    def cargar_senalados(self, claves: Iterable[str]) -> None:
        claves = list(claves)
        self.senalados = BloomFilter(len(claves), self.tasa_fp)
        for clave in claves:
            self.senalados.agregar(clave)
            self.senalados_exacto.add(clave)

    def consumir(self, ev: Event) -> Alerta | None:
        """Devuelve una Alerta si la tarjeta está señalada o supera el umbral en la ventana."""
        if ev.event_type != "purchase" or ev.card_id is None:
            return None
        # Ventana fija que avanza con el tiempo del evento.
        if self.inicio_ventana is None or (ev.event_time - self.inicio_ventana).total_seconds() >= self.ventana_seg:
            self.inicio_ventana = ev.event_time
            self.intensidad.reiniciar()
            self.ventanas += 1
        # Se cuenta antes de decidir: un intento bloqueado sigue siendo un intento.
        self.intensidad.agregar(ev.card_id)
        conteo = self.intensidad.estimar(ev.card_id)
        if ev.card_id in self.senalados:
            tipo = "senalada"
        elif conteo > self.umbral:
            tipo = "intensidad"
        else:
            return None
        self.alertas[tipo] += 1
        return Alerta(tipo, ev.card_id, conteo, ev)

    def verificar(self, alerta: Alerta) -> bool:
        """True si la alerta se confirma (no era un falso positivo del Bloom Filter)."""
        confirmada = alerta.tipo == "intensidad" or alerta.clave in self.senalados_exacto
        if confirmada:
            self.confirmadas += 1
        else:
            self.falsos_positivos += 1
        return confirmada

    def metricas(self) -> dict[str, Any]:
        """Alertas por tipo, confirmadas, falsos positivos y tamaño de las estructuras."""
        return {
            "alertas": dict(self.alertas),
            "confirmadas": self.confirmadas,
            "falsos_positivos": self.falsos_positivos,
            "ventanas": self.ventanas,
            "bits_bloom": self.senalados.m if self.senalados else 0,
            "k_bloom": self.senalados.k if self.senalados else 0,
            "contadores_cms": self.intensidad.ancho * self.intensidad.profundidad,
        }
