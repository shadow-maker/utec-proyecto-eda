"""Etapa 7 - Prueba final de HNSW contra KNN exacto.

Ejecutar desde la raiz del proyecto:
    python -m pipeline_eda.probar_etapa7_cierre_hnsw

No usa tracemalloc durante el benchmark.
"""

import csv
import gc
import random
import statistics
import time
from pathlib import Path

from pipeline_eda.etapa5_kdtree import knn_exacto
from pipeline_eda.etapa7_similitud import HNSW

# Configuracion final
TAMANOS = [100_000]
CONSULTAS = 100
K = 5
SEED = 42
M = 16
EF_CONSTRUCCION = 100
VALORES_EF = [50, 100, 200, 500, 1000]
UMBRAL_RECALL = 0.90
CARPETA_RESULTADOS = Path("resultados_etapa7")


def generar_productos(n):
    rng = random.Random(SEED)
    categorias = [2103807459595380000 + i for i in range(100)]
    return {
        product_id: (rng.random(), rng.choice(categorias))
        for product_id in range(1, n + 1)
    }


def construir_hnsw(productos):
    indice = HNSW(m=M, ef_construccion=EF_CONSTRUCCION, seed=SEED)
    for product_id, vector in productos.items():
        indice.insertar(product_id, vector)
    return indice


def guardar_csv(ruta, filas, campos):
    with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)


def ejecutar_prueba(n):
    print("\n" + "=" * 78)
    print(f"CIERRE HNSW VS KNN EXACTO - {n:,} PRODUCTOS")
    print("=" * 78)
    productos = generar_productos(n)
    if n <= K or CONSULTAS <= 0:
        raise ValueError("Se requieren mas de K productos y al menos una consulta")
    print(f"Productos: {n:,} | Categorias: {len({p[1] for p in productos.values()})}")
    print(f"Consultas: {min(CONSULTAS, n)} | K: {K} | M: {M} | ef_construccion: {EF_CONSTRUCCION}")

    print("\n[1/4] Construyendo HNSW (sin tracemalloc)...")
    gc.collect()
    inicio = time.perf_counter()
    hnsw = construir_hnsw(productos)
    construccion_s = time.perf_counter() - inicio
    print(f"Construccion: {construccion_s:.4f} s | Nivel maximo: {hnsw.nivel_maximo}")

    print("\n[2/4] Calculando KNN exacto...")
    rng = random.Random(SEED)
    ids_consulta = rng.sample(list(productos), min(CONSULTAS, n))
    ids = list(productos)
    puntos = list(productos.values())
    referencias = {}
    tiempos_exacto = []
    for product_id in ids_consulta:
        q = productos[product_id]
        inicio = time.perf_counter()
        exactos = [
            (distancia, candidato)
            for distancia, candidato in knn_exacto(puntos, ids, q, K + 1)
            if candidato != product_id
        ][:K]
        tiempos_exacto.append(time.perf_counter() - inicio)
        referencias[product_id] = {candidato for _, candidato in exactos}
    mediana_exacto = statistics.median(tiempos_exacto)
    print(f"KNN exacto: {mediana_exacto * 1000:.4f} ms (mediana)")

    print("\n[3/4] Comparando parametros ef...")
    print(f"{'EF':>6} {'HNSW ms':>12} {'Aceleracion':>14} {'Recall@5':>12} {'Nodos':>10}")
    print("-" * 62)
    filas = []
    detalle = []
    for ef in VALORES_EF:
        tiempos = []
        recalls = []
        nodos = []
        for product_id in ids_consulta:
            q = productos[product_id]
            inicio = time.perf_counter()
            aproximados = [
                (distancia, candidato)
                for distancia, candidato in hnsw.buscar(q, K + 1, ef=ef)
                if candidato != product_id
            ][:K]
            tiempo_ms = (time.perf_counter() - inicio) * 1000
            ids_aprox = {candidato for _, candidato in aproximados}
            ids_exacto = referencias[product_id]
            recall = len(ids_aprox & ids_exacto) / len(ids_exacto) if ids_exacto else 1.0
            tiempos.append(tiempo_ms)
            recalls.append(recall)
            nodos.append(hnsw.nodos_visitados)
            detalle.append({
                "productos": n,
                "ef": ef,
                "producto_consulta": product_id,
                "tiempo_hnsw_ms": round(tiempo_ms, 6),
                "recall": round(recall, 6),
                "nodos_visitados": hnsw.nodos_visitados,
            })
        mediana_hnsw = statistics.median(tiempos)
        aceleracion = mediana_exacto * 1000 / mediana_hnsw if mediana_hnsw else 0
        recall_promedio = statistics.mean(recalls)
        nodos_mediana = statistics.median(nodos)
        fila = {
            "productos": n,
            "consultas": len(ids_consulta),
            "k": K,
            "m": M,
            "ef_construccion": EF_CONSTRUCCION,
            "ef_busqueda": ef,
            "construccion_s": round(construccion_s, 6),
            "nivel_maximo": hnsw.nivel_maximo,
            "knn_exacto_mediana_ms": round(mediana_exacto * 1000, 6),
            "hnsw_mediana_ms": round(mediana_hnsw, 6),
            "aceleracion": round(aceleracion, 6),
            "recall_promedio": round(recall_promedio, 6),
            "nodos_mediana": nodos_mediana,
        }
        filas.append(fila)
        print(f"{ef:>6} {mediana_hnsw:>12.4f} {aceleracion:>13.2f}x {recall_promedio:>11.2%} {nodos_mediana:>10.0f}")

    print("\n[4/4] Guardando resultados...")
    CARPETA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    ruta_resumen = CARPETA_RESULTADOS / f"hnsw_resumen_{n}.csv"
    ruta_detalle = CARPETA_RESULTADOS / f"hnsw_detalle_{n}.csv"
    guardar_csv(ruta_resumen, filas, list(filas[0]))
    guardar_csv(ruta_detalle, detalle, list(detalle[0]))

    candidatos = [fila for fila in filas if fila["recall_promedio"] >= UMBRAL_RECALL]
    print("\n" + "=" * 78)
    print("CONCLUSIONES AUTOMATICAS")
    print("=" * 78)
    print(f"Construccion: {construccion_s:.4f} s")
    print(f"KNN exacto: {mediana_exacto * 1000:.4f} ms")
    if candidatos:
        recomendado = min(candidatos, key=lambda fila: fila["hnsw_mediana_ms"])
        print(f"Configuracion mas rapida con Recall >= {UMBRAL_RECALL:.0%}: ef={recomendado['ef_busqueda']}")
        print(f"Recall@{K}: {recomendado['recall_promedio']:.2%}")
        print(f"Aceleracion: {recomendado['aceleracion']:.2f}x")
    else:
        mejor = max(filas, key=lambda fila: fila["recall_promedio"])
        print(f"No se alcanzo Recall >= {UMBRAL_RECALL:.0%}.")
        print(f"Mayor Recall@{K}: {mejor['recall_promedio']:.2%} con ef={mejor['ef_busqueda']}")
    print(f"Resumen CSV: {ruta_resumen}")
    print(f"Detalle CSV: {ruta_detalle}")
    print("Nota: memoria no medida; datos sinteticos y un solo seed.")
    print("PRUEBA FINALIZADA")


if __name__ == "__main__":
    for tamano in TAMANOS:
        ejecutar_prueba(tamano)
