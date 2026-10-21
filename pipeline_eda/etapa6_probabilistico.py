"""Etapa 6 [FIJA] — Filtrado probabilístico (responsable: A).

Estructuras: Bloom Filter para tarjetas/cuentas señaladas y
Count-Min Sketch para la intensidad de intentos en una ventana temporal.
Un positivo del Bloom Filter se verifica contra el conjunto exacto antes de
bloquear la operación.
"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable
from typing import Any

from .evento import Alerta, Event


class BloomFilter:
    """m bits y k funciones hash, calculados a partir de n esperado y tasa de FP."""

    def __init__(self, n_esperado: int, tasa_fp: float) -> None:
        self.n_esperado = n_esperado
        self.tasa_fp = tasa_fp

    def agregar(self, clave: str) -> None:
        raise NotImplementedError

    def __contains__(self, clave: str) -> bool:
        raise NotImplementedError


class CountMinSketch:
    """Matriz profundidad × ancho de contadores. Puede sobreestimar, nunca subestimar."""

    def __init__(self, ancho: int, profundidad: int, seed: int = 0) -> None:
        self.ancho = ancho
        self.profundidad = profundidad
        self.seed = seed

    def agregar(self, clave: str, cantidad: int = 1) -> None:
        raise NotImplementedError

    def estimar(self, clave: str) -> int:
        raise NotImplementedError

    def reiniciar(self) -> None:
        """Vacía los contadores al empezar una nueva ventana."""
        raise NotImplementedError


class DetectorFraude:
    nombre = "etapa6_probabilistico"

    def __init__(
        self,
        ventana_seg: int = 300,
        umbral: int = 5,
        n_esperado: int = 100_000,
        tasa_fp: float = 0.01,
        ancho_cms: int = 2_000,
        profundidad_cms: int = 5,
        seed: int = 42,
    ) -> None:
        self.ventana_seg = ventana_seg
        self.umbral = umbral
        self.senalados = BloomFilter(n_esperado, tasa_fp)
        self.senalados_exacto: set[str] = set()  # solo para verificar positivos
        self.intensidad = CountMinSketch(ancho_cms, profundidad_cms, seed)

    def cargar_senalados(self, claves: Iterable[str]) -> None:
        raise NotImplementedError

    def consumir(self, ev: Event) -> Alerta | None:
        """Devuelve una Alerta si la tarjeta/cuenta está señalada o supera el umbral."""
        raise NotImplementedError

    def verificar(self, alerta: Alerta) -> bool:
        """True si la alerta se confirma (no era un falso positivo)."""
        raise NotImplementedError

    def metricas(self) -> dict[str, Any]:
        """Alertas emitidas, confirmadas, falsos positivos, memoria vs. estructura exacta."""
        raise NotImplementedError
