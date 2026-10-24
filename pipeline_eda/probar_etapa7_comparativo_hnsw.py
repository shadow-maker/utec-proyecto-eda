
"""Etapa 7 — Benchmark HNSW vs. KNN exacto de la etapa 5.

Compara tiempo de construcción, velocidad de búsqueda y Recall@5.
La construcción se mide sin tracemalloc para evitar su sobrecarga.
"""

import gc
import random
import statistics
import time

from pipeline_eda.etapa7_similitud import HNSW
from pipeline_eda.etapa5_kdtree import knn_exacto


# ============================================================
# 1. CONFIGURACIÓN
# ============================================================

TAMANOS = [50_000]
CONSULTAS = 100
K = 5
SEED = 42

M = 16
EF_CONSTRUCCION = 100
VALORES_EF = [50, 100, 200, 500]


# ============================================================
# 2. GENERACIÓN DE PRODUCTOS
# ============================================================

def generar_productos(n):
    """Genera productos sintéticos con precio y categoría."""

    rng = random.Random(SEED)

    # Simulamos 100 categorías.
    categorias = [
        2103807459595380000 + i
        for i in range(100)
    ]

    productos = {}

    for id_ in range(1, n + 1):
        precio = rng.random()
        categoria = rng.choice(categorias)

        productos[id_] = (precio, categoria)

    return productos


# ============================================================
# 3. CONSTRUCCIÓN DEL HNSW
# ============================================================

def construir_hnsw(productos):
    """Construye el índice HNSW con todos los productos."""

    indice = HNSW(
        m=M,
        ef_construccion=EF_CONSTRUCCION,
        seed=SEED
    )

    for id_, vector in productos.items():
        indice.insertar(id_, vector)

    return indice


# ============================================================
# 4. PRUEBA COMPARATIVA
# ============================================================

def ejecutar_prueba(n):

    print("\n" + "=" * 75)
    print(f"PRUEBA HNSW VS KNN EXACTO CON {n:,} PRODUCTOS")
    print("=" * 75)

    productos = generar_productos(n)

    print(f"Productos generados: {len(productos):,}")
    print(
        "Categorías distintas:",
        len(set(v[1] for v in productos.values()))
    )
    print(f"Consultas: {CONSULTAS}")
    print(f"K: {K}")

    # --------------------------------------------------------
    # 4.1. CONSTRUCCIÓN HNSW SIN TRACEMALLOC
    # --------------------------------------------------------

    print("\nConstruyendo HNSW...")

    gc.collect()

    inicio = time.perf_counter()

    hnsw = construir_hnsw(productos)

    tiempo_construccion = time.perf_counter() - inicio

    print(f"Construcción HNSW: {tiempo_construccion:.4f} s")
    print("Memoria pico construcción: No medida en esta ejecución")
    print(f"Nivel máximo del grafo: {hnsw.nivel_maximo}")

    # --------------------------------------------------------
    # 4.2. PREPARAR CONSULTAS
    # --------------------------------------------------------

    rng = random.Random(SEED)

    ids_consulta = rng.sample(
        list(productos.keys()),
        min(CONSULTAS, len(productos))
    )

    ids = list(productos.keys())
    puntos = list(productos.values())

    # --------------------------------------------------------
    # 4.3. KNN EXACTO: LÍNEA BASE
    # --------------------------------------------------------

    print("\nCalculando KNN exacto...")

    referencias = {}
    tiempos_exacto = []

    for id_consulta in ids_consulta:

        q = productos[id_consulta]

        inicio = time.perf_counter()

        exactos = [
            (distancia, id_)
            for distancia, id_ in knn_exacto(
                puntos, ids, q, K + 1
            )
            if id_ != id_consulta
        ][:K]

        tiempo = time.perf_counter() - inicio

        tiempos_exacto.append(tiempo)

        referencias[id_consulta] = {
            id_ for _, id_ in exactos
        }

    mediana_exacto = statistics.median(tiempos_exacto)

    print(f"KNN exacto mediana: {mediana_exacto * 1000:.4f} ms")

    # --------------------------------------------------------
    # 4.4. HNSW CON DIFERENTES VALORES DE EF
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("RESULTADOS COMPARATIVOS")
    print("=" * 75)

    print(
        f"{'EF':>6} "
        f"{'HNSW (ms)':>12} "
        f"{'Aceleración':>14} "
        f"{'Recall@5':>12} "
        f"{'Nodos':>10}"
    )

    print("-" * 75)

    resultados = []

    for ef in VALORES_EF:

        tiempos_hnsw = []
        recalls = []
        nodos_visitados = []

        for id_consulta in ids_consulta:

            q = productos[id_consulta]

            inicio = time.perf_counter()

            aproximados = [
                (distancia, id_)
                for distancia, id_ in hnsw.buscar(
                    q, K + 1, ef=ef
                )
                if id_ != id_consulta
            ][:K]

            tiempo = time.perf_counter() - inicio

            tiempos_hnsw.append(tiempo)

            ids_hnsw = {
                id_ for _, id_ in aproximados
            }

            ids_exactos = referencias[id_consulta]

            recall = (
                len(ids_hnsw & ids_exactos)
                / len(ids_exactos)
                if ids_exactos else 1.0
            )

            recalls.append(recall)
            nodos_visitados.append(hnsw.nodos_visitados)

        mediana_hnsw = statistics.median(tiempos_hnsw)

        aceleracion = (
            mediana_exacto / mediana_hnsw
            if mediana_hnsw > 0 else 0
        )

        recall_promedio = statistics.mean(recalls)

        nodos_mediana = statistics.median(
            nodos_visitados
        )

        resultados.append({
            "ef": ef,
            "tiempo_ms": mediana_hnsw * 1000,
            "aceleracion": aceleracion,
            "recall": recall_promedio,
            "nodos": nodos_mediana
        })

        print(
            f"{ef:>6} "
            f"{mediana_hnsw * 1000:>12.4f} "
            f"{aceleracion:>13.2f}x "
            f"{recall_promedio:>11.2%} "
            f"{nodos_mediana:>10.0f}"
        )

    # --------------------------------------------------------
    # 4.5. RESUMEN FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 75)
    print("RESUMEN FINAL")
    print("=" * 75)

    mejor_recall = max(
        resultados,
        key=lambda r: r["recall"]
    )

    mas_rapido = min(
        resultados,
        key=lambda r: r["tiempo_ms"]
    )

    print(f"Productos evaluados: {n:,}")
    print(f"Consultas realizadas: {len(ids_consulta)}")
    print(f"Tiempo de construcción: {tiempo_construccion:.4f} s")
    print("Memoria pico: No medida en esta ejecución")
    print(f"KNN exacto: {mediana_exacto * 1000:.4f} ms")

    print(
        f"\nMayor Recall@{K}: "
        f"{mejor_recall['recall']:.2%} "
        f"(ef={mejor_recall['ef']})"
    )

    print(
        f"Menor tiempo HNSW: "
        f"{mas_rapido['tiempo_ms']:.4f} ms "
        f"(ef={mas_rapido['ef']})"
    )

    # Seleccionamos la configuración más rápida
    # entre las que alcancen al menos 90% de recall.

    candidatos = [
        r for r in resultados
        if r["recall"] >= 0.90
    ]

    if candidatos:

        recomendado = min(
            candidatos,
            key=lambda r: r["tiempo_ms"]
        )

        print(
            f"\nMejor configuración con Recall >= 90%: "
            f"ef={recomendado['ef']}"
        )

        print(
            f"Aceleración: "
            f"{recomendado['aceleracion']:.2f}x"
        )

    else:

        print(
            "\nNinguna configuración alcanzó "
            "un Recall@5 del 90%."
        )

        print(
            "Será necesario revisar la construcción "
            "y selección de vecinos del grafo HNSW."
        )

    print("\nPRUEBA FINALIZADA")


# ============================================================
# 5. EJECUCIÓN
# ============================================================

if __name__ == "__main__":

    for n in TAMANOS:
        ejecutar_prueba(n)
