
import gc
import random
import statistics
import time

from pipeline_eda.etapa5_kdtree import KDTree, knn_exacto


K = 10
NUM_CONSULTAS = 5
TAMANOS = [100_000, 500_000]
SEMILLA = 42


def estadisticas(tiempos):
    return {
        "promedio": statistics.mean(tiempos),
        "mediana": statistics.median(tiempos),
        "minimo": min(tiempos),
        "maximo": max(tiempos),
    }


def probar_volumen(n, semilla):
    rng = random.Random(semilla)

    print("\n" + "=" * 65)
    print(f"BENCHMARK CON {n:,} PRODUCTOS")
    print("=" * 65)

    # Generar datos sintéticos reproducibles.
    puntos = [
        (rng.uniform(0, 100), rng.uniform(0, 100))
        for _ in range(n)
    ]
    ids = list(range(1, n + 1))

    # Construir el KD-Tree.
    arbol = KDTree()

    inicio = time.perf_counter()
    arbol.construir(puntos, ids)
    tiempo_construccion = time.perf_counter() - inicio

    tiempos_kd = []
    tiempos_exacto = []
    nodos_visitados = []
    todas_coinciden = True

    for numero in range(NUM_CONSULTAS):
        consulta = (
            rng.uniform(0, 100),
            rng.uniform(0, 100),
        )

        inicio = time.perf_counter()
        resultado_kd = arbol.knn(consulta, K)
        tiempo_kd_consulta = time.perf_counter() - inicio

        nodos_visitados.append(arbol.nodos_visitados)

        inicio = time.perf_counter()
        resultado_exacto = knn_exacto(
            puntos, ids, consulta, K
        )
        tiempo_exacto_consulta = time.perf_counter() - inicio

        tiempos_kd.append(tiempo_kd_consulta)
        tiempos_exacto.append(tiempo_exacto_consulta)

        coincide = resultado_kd == resultado_exacto
        todas_coinciden = todas_coinciden and coincide

        print(
            f"Consulta {numero + 1}: "
            f"coinciden={coincide}, "
            f"nodos visitados={arbol.nodos_visitados:,}"
        )

    kd = estadisticas(tiempos_kd)
    exacto = estadisticas(tiempos_exacto)

    print("\n--- TIEMPO DE CONSTRUCCIÓN ---")
    print(f"KD-Tree: {tiempo_construccion:.4f} segundos")

    print("\n--- TIEMPOS DE CONSULTA (milisegundos) ---")
    print(
        f"{'Estadística':<12}"
        f"{'KD-Tree':>14}"
        f"{'KNN exacto':>16}"
    )

    for nombre, clave in [
        ("Promedio", "promedio"),
        ("Mediana", "mediana"),
        ("Mínimo", "minimo"),
        ("Máximo", "maximo"),
    ]:
        print(
            f"{nombre:<12}"
            f"{kd[clave] * 1000:>14.4f}"
            f"{exacto[clave] * 1000:>16.4f}"
        )

    if kd["mediana"] > 0:
        velocidad = exacto["mediana"] / kd["mediana"]
        print(f"\nFactor de velocidad por mediana: {velocidad:.2f}x")

    print(
        f"Promedio de nodos visitados: "
        f"{statistics.mean(nodos_visitados):,.1f} de {n:,}"
    )
    print(
        f"Porcentaje promedio de nodos visitados: "
        f"{100 * statistics.mean(nodos_visitados) / n:.4f}%"
    )
    print(f"¿Todas las consultas coinciden?: {todas_coinciden}")

    # Liberar memoria antes de probar el siguiente volumen.
    del arbol, puntos, ids
    gc.collect()


if __name__ == "__main__":
    for n in TAMANOS:
        probar_volumen(n, SEMILLA + n)
