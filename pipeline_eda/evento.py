"""Contrato de datos del pipeline: los tipos que intercambian todas las etapas."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum


class Prioridad(IntEnum):
    """Menor valor = se atiende antes (el heap de la etapa 2 es de mínimos)."""

    ALERTA = 0
    EXPRESS = 1
    ESTANDAR = 2
    PROGRAMADA = 3
    NAVEGACION = 4  # view / cart: no hay orden asociada


@dataclass(slots=True)
class Event:
    # --- Campos reales (REES46) ---
    event_time: datetime  # con zona horaria UTC
    event_type: str  # "view" | "cart" | "purchase"
    product_id: int
    category_id: int
    category_code: str | None
    brand: str | None
    price: float
    user_id: int
    user_session: str | None  # vacía en algunas filas del CSV
    # --- Campos sintéticos (los genera la etapa 0) ---
    order_id: str | None = None  # solo purchase: = user_session (una orden = las compras de una sesión)
    tipo_envio: str | None = None  # "express" | "estandar" | "programada"; solo purchase
    card_id: str | None = None  # solo purchase
    # --- Verdad de referencia: SOLO para evaluar; el pipeline no debe leerlos ---
    is_fraud: bool = False
    is_dup: bool = False


@dataclass(slots=True)
class Producto:
    """Entrada del catálogo (etapas 3, 4, 5 y 7).

    El precio de un producto cambia entre eventos: `price` es el último visto,
    y quien lo indexe (p. ej. el B+Tree de la etapa 4) debe manejar actualizaciones.
    """

    product_id: int
    category_id: int
    category_code: str | None
    brand: str | None
    price: float  # último precio visto

    @classmethod
    def desde_evento(cls, ev: Event) -> Producto:
        return cls(ev.product_id, ev.category_id, ev.category_code, ev.brand, ev.price)


@dataclass(slots=True)
class Alerta:
    """Salida de la etapa 6. Vuelve al heap de la etapa 2 con Prioridad.ALERTA."""

    tipo: str  # "senalada" (Bloom Filter) | "intensidad" (Count-Min Sketch)
    clave: str  # card_id
    conteo_estimado: int  # Count-Min Sketch en la ventana actual
    evento: Event  # operación retenida hasta verificar la alerta
