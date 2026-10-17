"""Generador del componente sintético (fila A del plan — todos).

Toma el CSV real de REES46 y escribe un CSV enriquecido con los campos que el
dataset no trae (orden, tipo de envío, tarjeta, dispositivo), duplicados y
ráfagas de fraude inyectadas, siempre con semilla fija.
"""
from __future__ import annotations

import csv
import random
from collections.abc import Iterator
from pathlib import Path

from .etapa0_ingesta import leer_csv
from .evento import Event

DIR_DATOS = Path(__file__).resolve().parents[1] / "data"

TAMANOS = {
    "1K": 1_000,
    "10K": 10_000,
    "100K": 100_000,
    "1M": 1_000_000,
    "10M": 10_000_000,
}


def enriquecer(fila: list[str], rng: random.Random) -> Event | None:
    """Convierte una fila real en Event y agrega los campos sintéticos.

    Devuelve None si la fila está malformada.
    """
    raise NotImplementedError


def generar_dataset(
    origen: Path,
    tamano: str,
    seed: int = 42,
    tasa_dup: float = 0.02,
    tasa_fraude: float = 0.001,
) -> None:
    """Escribe `ruta_dataset(tamano)` y `ruta_senalados(tamano)` a partir del CSV real."""
    raise NotImplementedError


def ruta_dataset(tamano: str) -> Path:
    return DIR_DATOS / f"eventos_{tamano}.csv"


def ruta_senalados(tamano: str) -> Path:
    return DIR_DATOS / f"senalados_{tamano}.txt"


def cargar_dataset(tamano: str) -> Iterator[Event]:
    """Stream perezoso de eventos enriquecidos para un tamaño de TAMANOS."""
    return leer_csv(ruta_dataset(tamano))


def cargar_senalados(tamano: str) -> list[str]:
    """Tarjetas, dispositivos y cuentas señaladas de antemano (entrada de la etapa 6)."""
    raise NotImplementedError
