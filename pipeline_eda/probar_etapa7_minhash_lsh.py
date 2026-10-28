
from pipeline_eda.etapa7_similitud import (
    jaccard_exacto,
    MinHash,
    LSH
)

print("=== PRUEBA 1: JACCARD EXACTO ===")

usuarios_a = {101, 102, 103, 104}
usuarios_b = {101, 102, 105}
usuarios_c = {201, 202, 203}

print("A vs B:", jaccard_exacto(usuarios_a, usuarios_b))
print("A vs C:", jaccard_exacto(usuarios_a, usuarios_c))

assert jaccard_exacto(usuarios_a, usuarios_b) == 0.4
assert jaccard_exacto(usuarios_a, usuarios_c) == 0.0


print("\n=== PRUEBA 2: MINHASH ===")

minhash = MinHash(num_permutaciones=128, seed=42)

firma_a = minhash.firma(usuarios_a)
firma_b = minhash.firma(usuarios_b)
firma_c = minhash.firma(usuarios_c)

def similitud_firmas(a, b):
    coincidencias = sum(
        x == y for x, y in zip(a, b)
    )
    return coincidencias / len(a)

print("Jaccard real A-B:", jaccard_exacto(usuarios_a, usuarios_b))
print("MinHash estimado A-B:", similitud_firmas(firma_a, firma_b))

print("Jaccard real A-C:", jaccard_exacto(usuarios_a, usuarios_c))
print("MinHash estimado A-C:", similitud_firmas(firma_a, firma_c))


print("\n=== PRUEBA 3: LSH ===")

lsh = LSH(bandas=32, filas=4)

lsh.insertar(1, firma_a)
lsh.insertar(2, firma_b)
lsh.insertar(3, firma_c)

print("Candidatos producto A:", lsh.candidatos(firma_a))
print("Candidatos producto B:", lsh.candidatos(firma_b))

assert 1 in lsh.candidatos(firma_a)

print("\nPRUEBAS BÁSICAS COMPLETADAS")


"""Comparación MinHash + LSH vs Jaccard exacto."""

import random
import time
import tracemalloc
from collections import defaultdict

from pipeline_eda.etapa7_similitud import (
    MinHash,
    LSH,
    jaccard_exacto,
)

TAMANOS = [10_000, 100_000, 500_000]
CONSULTAS = 20
K = 5
PERMUTACIONES = 128
BANDAS = 32
SEED = 42


def generar_datos(n_eventos):
    """Genera interacciones usuario-producto.

    Cada producto pertenece a un grupo de afinidad.
    Los usuarios tienden a interactuar con productos
    de su mismo grupo, creando similitudes medibles.
    """
    rng = random.Random(SEED)

    n_productos = max(100, n_eventos // 100)
    n_usuarios = max(200, n_eventos // 20)
    n_grupos = max(5, n_productos // 50)

    conjuntos = defaultdict(set)

    for _ in range(n_eventos):
        producto = rng.randrange(n_productos)
        grupo = producto % n_grupos

        # 85% de eventos dentro de un grupo de afinidad.
        if rng.random() < 0.85:
            usuario = (
                grupo * 20
                + rng.randrange(20)
            )
        else:
            usuario = rng.randrange(n_usuarios)

        conjuntos[producto].add(usuario)

    return dict(conjuntos), n_usuarios


def construir_indice(conjuntos):
    minhash = MinHash(
        num_permutaciones=PERMUTACIONES,
        seed=SEED
    )
    lsh = LSH(
        bandas=BANDAS,
        filas=PERMUTACIONES // BANDAS
    )

    firmas = {}

    for producto, usuarios in conjuntos.items():
        firma = minhash.firma(usuarios)
        firmas[producto] = firma
        lsh.insertar(producto, firma)

    return lsh, firmas


def buscar_exacto(conjuntos, producto, k):
    """Compara el producto contra todos los demás."""
    usuarios = conjuntos[producto]

    resultados = []

    for otro, otros_usuarios in conjuntos.items():
        if otro == producto:
            continue

        similitud = jaccard_exacto(
            usuarios,
            otros_usuarios
        )

        if similitud > 0:
            resultados.append((similitud, otro))

    resultados.sort(key=lambda x: (-x[0], x[1]))

    return [id_ for _, id_ in resultados[:k]]


def buscar_lsh(conjuntos, lsh, firmas, producto, k):
    """Busca candidatos y los ordena con Jaccard."""
    candidatos = lsh.candidatos(firmas[producto])
    candidatos.discard(producto)

    resultados = []

    for otro in candidatos:
        similitud = jaccard_exacto(
            conjuntos[producto],
            conjuntos[otro]
        )

        if similitud > 0:
            resultados.append((similitud, otro))

    resultados.sort(key=lambda x: (-x[0], x[1]))

    return (
        [id_ for _, id_ in resultados[:k]],
        len(candidatos)
    )


def ejecutar_prueba(n_eventos):
    print(f"\n{'=' * 60}")
    print(f"PRUEBA CON {n_eventos:,} EVENTOS")
    print(f"{'=' * 60}")

    conjuntos, n_usuarios = generar_datos(n_eventos)

    print("Productos distintos:", len(conjuntos))
    print("Usuarios posibles:", n_usuarios)

    tracemalloc.start()
    inicio = time.perf_counter()

    lsh, firmas = construir_indice(conjuntos)

    tiempo_construccion = time.perf_counter() - inicio

    _, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"Construcción LSH: {tiempo_construccion:.4f} s")
    print(f"Memoria pico construcción: {memoria_pico / 1024**2:.2f} MB")

    rng = random.Random(SEED)
    productos = list(conjuntos)

    consultas = rng.sample(
        productos,
        min(CONSULTAS, len(productos))
    )

    tiempos_exacto = []
    tiempos_lsh = []
    recalls = []
    candidatos_totales = []

    for producto in consultas:

        inicio = time.perf_counter()
        exactos = buscar_exacto(conjuntos, producto, K)
        tiempos_exacto.append(time.perf_counter() - inicio)

        inicio = time.perf_counter()
        aproximados, n_candidatos = buscar_lsh(
            conjuntos, lsh, firmas, producto, K
        )
        tiempos_lsh.append(time.perf_counter() - inicio)

        if exactos:
            recall = (
                len(set(exactos) & set(aproximados))
                / len(exactos)
            )
        else:
            recall = 1.0 if not aproximados else 0.0

        recalls.append(recall)
        candidatos_totales.append(n_candidatos)

    promedio_exacto = sum(tiempos_exacto) / len(tiempos_exacto)
    promedio_lsh = sum(tiempos_lsh) / len(tiempos_lsh)

    print(f"\nConsultas realizadas: {len(consultas)}")
    print(f"Jaccard exacto promedio: {promedio_exacto * 1000:.3f} ms")
    print(f"MinHash + LSH promedio: {promedio_lsh * 1000:.3f} ms")

    if promedio_lsh > 0:
        print(f"Aceleración: {promedio_exacto / promedio_lsh:.2f}x")

    print(f"Recall@{K} promedio: {sum(recalls) / len(recalls):.2%}")
    print(
        "Candidatos promedio:",
        f"{sum(candidatos_totales) / len(candidatos_totales):.1f}"
    )


if __name__ == "__main__":
    for n in TAMANOS:
        ejecutar_prueba(n)
