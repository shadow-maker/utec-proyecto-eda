"""Orquestador del pipeline (filas E y G del plan — todos).

Único módulo que conoce a todas las etapas y las conecta:

    fuente → 0 sintético + buffer → 1 dedup → 2 heap → despachador ─┬→ 6 fraude ─ alerta → 2 heap
                                                                    ├→ 3 catálogo / LRU
                                                                    ├→ 4 B+Tree
                                                                    ├→ 7 similitud
                                                                    ├→ 8 grafo
                                                                    └→ 9 servicio
    al cerrar: 5 KD-Tree y HNSW (7) se construyen con el catálogo de la etapa 3.

Regla del proyecto: un módulo de etapa solo importa `evento`, nunca otro módulo
de etapa. Toda etapa expone `nombre` y `metricas()`, que se usan en `metricas()`.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from .etapa0_ingesta import Ingesta
from .etapa1_preproceso import Preprocesador
from .etapa2_prioridad import ColaPrioridad
from .etapa3_cache import CatalogoCache
from .etapa4_bplustree import IndiceProductos
from .etapa5_kdtree import IndiceKD, distancia_mixta
from .etapa6_probabilistico import DetectorFraude
from .etapa7_similitud import Similitud
from .etapa8_grafo import GrafoCoCompra
from .etapa9_servicio import Servicio
from .evento import Alerta, Event


@dataclass
class Config:
    seed: int = 42  # etapas 6–8; los datos sintéticos usan SEMILLA de la etapa 0
    capacidad_buffer: int = 50_000
    tam_lote: int = 10_000
    ventana_dedup: int = 100_000
    capacidad_lru: int = 10_000
    orden_bplus: int = 64
    ventana_fraude_seg: int = 300
    umbral_fraude: int = 5
    tasa_fp_bloom: float = 0.01
    k: int = 10


class Pipeline:
    def __init__(self, config: Config | None = None) -> None:
        c = self.config = config or Config()
        self.e0 = Ingesta(c.capacidad_buffer, c.tam_lote)
        self.e1 = Preprocesador(c.ventana_dedup)
        self.e2 = ColaPrioridad()
        self.e3 = CatalogoCache(c.capacidad_lru)
        self.e4 = IndiceProductos(c.orden_bplus)
        self.e5 = IndiceKD()
        self.e6 = DetectorFraude(
            ventana_seg=c.ventana_fraude_seg,
            umbral=c.umbral_fraude,
            tasa_fp=c.tasa_fp_bloom,
            seed=c.seed,
        )
        self.e7 = Similitud(distancia_mixta, seed=c.seed)  # HNSW usa la misma distancia que el KD-Tree
        self.e8 = GrafoCoCompra(seed=c.seed)
        self.e9 = Servicio(self.e3, self.e5, self.e7, self.e8, k=c.k)

    def etapas(self) -> list[Any]:
        return [self.e0, self.e1, self.e2, self.e3, self.e4,
                self.e5, self.e6, self.e7, self.e8, self.e9]

    def run(self, fuente: Iterable[Event]) -> None:
        """`fuente`: eventos reales (p. ej. leer_csv); la etapa 0 agrega lo sintético."""
        self.e6.cargar_senalados(self.e0.senalados())
        for lote in self.e0.lotes(fuente):
            for ev in self.e1.procesar(lote):
                self.e2.push_evento(ev)
            self._drenar_heap()
        self._cerrar()

    def _drenar_heap(self) -> None:
        while len(self.e2):
            item = self.e2.pop()
            if isinstance(item, Alerta):
                confirmada = self.e6.verificar(item)
                self.e9.registrar_alerta(item, confirmada)
                if not confirmada:  # falso positivo del Bloom: se libera la operación
                    self._despachar(item.evento)
                continue
            alerta = self.e6.consumir(item)
            if alerta is not None:  # se retiene la operación hasta verificar
                self.e2.push_alerta(alerta)
            else:
                self._despachar(item)

    def _despachar(self, ev: Event) -> None:
        self.e3.consumir(ev)
        self.e4.consumir(ev)
        self.e7.consumir(ev)
        self.e8.consumir(ev)
        self.e9.registrar_evento(ev)

    def _cerrar(self) -> None:
        self.e7.cerrar()
        productos = list(self.e3.productos())
        self.e5.construir(productos)
        # Los mismos vectores del KD-Tree, normalizados con el precio mínimo y máximo reales del catálogo.
        self.e7.construir_vectorial(dict(zip(self.e5.ids, self.e5.puntos)))

    def metricas(self) -> dict[str, dict[str, Any]]:
        return {e.nombre: e.metricas() for e in self.etapas()}
