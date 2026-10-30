"""Etapa 8 [FIJA] — Grafo de dominio (responsable: C).

Nodos = productos; arista ponderada = en cuántas órdenes se compraron juntos.
El grafo es no dirigido y se guarda como lista de adyacencia. Influencia con
PageRank (vs. ranking por grado) y comunidades con Label Propagation (vs.
componentes conexas).
"""
from __future__ import annotations

import random
from typing import Any

from .evento import Event


class GrafoCoCompra:
    nombre = "etapa8_grafo"

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.adyacencia: dict[int, dict[int, int]] = {}  # solo productos con al menos una arista
        self._ordenes: dict[str, set[int]] = {}  # order_id -> productos ya vistos
        self.iteraciones: dict[str, int] = {}  # de la última corrida de cada algoritmo

    def consumir(self, ev: Event) -> None:
        """En cada purchase, conecta el producto con los ya comprados en la misma orden."""
        if ev.event_type != "purchase" or ev.order_id is None:
            return
        productos = self._ordenes.setdefault(ev.order_id, set())
        p = ev.product_id
        if p in productos:  # el mismo producto dos veces en una orden no suma
            return
        for otro in productos:
            vecinos_p = self.adyacencia.setdefault(p, {})
            vecinos_otro = self.adyacencia.setdefault(otro, {})
            vecinos_p[otro] = vecinos_p.get(otro, 0) + 1
            vecinos_otro[p] = vecinos_otro.get(p, 0) + 1
        productos.add(p)

    def pagerank(
        self, amortiguacion: float = 0.85, max_iter: int = 100, tol: float = 1e-6
    ) -> dict[int, float]:
        """Método de potencias: PR(v) = (1-d)/N + d · Σ PR(u) · w(u,v) / w(u). O(iteraciones · aristas).

        Todo nodo tiene al menos una arista (w(u) > 0), así que no hay nodos colgantes.
        """
        d, n = amortiguacion, len(self.adyacencia)
        fuerza = {u: sum(vecinos.values()) for u, vecinos in self.adyacencia.items()}
        pr = {u: 1 / n for u in self.adyacencia}
        for iteracion in range(1, max_iter + 1):
            nuevo = {u: (1 - d) / n for u in self.adyacencia}
            for u, vecinos in self.adyacencia.items():
                reparto = d * pr[u] / fuerza[u]  # u reparte su puntaje según el peso de cada arista
                for v, w in vecinos.items():
                    nuevo[v] += reparto * w
            cambio = sum(abs(nuevo[u] - pr[u]) for u in self.adyacencia)
            pr = nuevo
            if cambio < tol:
                break
        self.iteraciones["pagerank"] = iteracion
        return pr

    def ranking_por_grado(self) -> list[tuple[int, float]]:
        """Línea base: grado ponderado de cada producto, de mayor a menor. O(aristas + N log N)."""
        grados = [(u, sum(vecinos.values())) for u, vecinos in self.adyacencia.items()]
        return sorted(grados, key=lambda x: (-x[1], x[0]))

    def comunidades(self, metodo: str = "label_propagation", seed: int | None = None) -> dict[int, int]:
        """product_id -> id de comunidad. metodo: "label_propagation" o "componentes"."""
        if metodo == "componentes":
            return self._componentes_conexas()
        return self._label_propagation(self.seed if seed is None else seed)

    def _label_propagation(self, seed: int, max_iter: int = 100) -> dict[int, int]:
        """Cada nodo adopta la etiqueta con más peso entre sus vecinos, en orden aleatorio,
        hasta que ninguno cambia. O(aristas) por vuelta."""
        rng = random.Random(seed)
        etiqueta = {u: u for u in self.adyacencia}  # cada producto empieza en su propia comunidad
        nodos = list(self.adyacencia)
        for vueltas in range(1, max_iter + 1):
            rng.shuffle(nodos)
            cambios = 0
            for u in nodos:
                votos: dict[int, int] = {}
                for v, w in self.adyacencia[u].items():
                    votos[etiqueta[v]] = votos.get(etiqueta[v], 0) + w
                maximo = max(votos.values())
                if votos.get(etiqueta[u]) == maximo:  # su etiqueta ya es ganadora: no cambia (evita oscilar)
                    continue
                etiqueta[u] = rng.choice([e for e, peso in votos.items() if peso == maximo])
                cambios += 1
            if cambios == 0:
                break
        self.iteraciones["label_propagation"] = vueltas
        return etiqueta

    def _componentes_conexas(self) -> dict[int, int]:
        """Alternativa simple: mismo grupo si hay algún camino entre los productos. DFS, O(N + aristas)."""
        etiqueta: dict[int, int] = {}
        for inicio in self.adyacencia:
            if inicio in etiqueta:
                continue
            etiqueta[inicio] = inicio
            pila = [inicio]
            while pila:
                u = pila.pop()
                for v in self.adyacencia[u]:
                    if v not in etiqueta:
                        etiqueta[v] = inicio
                        pila.append(v)
        return etiqueta

    def modularidad(self, particion: dict[int, int]) -> float:
        """Q = Σ_c [ L_c / m − (d_c / 2m)² ]: peso dentro de cada comunidad vs. el esperado al azar."""
        total = 0  # 2m: cada arista se cuenta desde sus dos extremos
        dentro: dict[int, int] = {}  # 2·L_c
        grado: dict[int, int] = {}  # d_c
        for u, vecinos in self.adyacencia.items():
            c = particion[u]
            for v, w in vecinos.items():
                total += w
                grado[c] = grado.get(c, 0) + w
                if particion[v] == c:
                    dentro[c] = dentro.get(c, 0) + w
        return sum(dentro.get(c, 0) / total - (grado[c] / total) ** 2 for c in grado)

    def metricas(self) -> dict[str, Any]:
        """Nodos, aristas, número y tamaño de comunidades, modularidad."""
        particion = self.comunidades()
        tamanos: dict[int, int] = {}
        for c in particion.values():
            tamanos[c] = tamanos.get(c, 0) + 1
        return {
            "ordenes": len(self._ordenes),
            "nodos": len(self.adyacencia),
            "aristas": sum(len(vecinos) for vecinos in self.adyacencia.values()) // 2,
            "comunidades": len(tamanos),
            "tamanos_mayores": sorted(tamanos.values(), reverse=True)[:5],
            "modularidad": round(self.modularidad(particion), 3),
            "iteraciones": dict(self.iteraciones),
        }
