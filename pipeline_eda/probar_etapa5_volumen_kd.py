import random
import time

from pipeline_eda.evento import Producto
from pipeline_eda.etapa5_kdtree import (
    IndiceKD,
    knn_exacto,
    vectorizar,
)

N = 10_000
K = 10
SEED = 42

random.seed(SEED)

# Generamos productos sintéticos reproducibles.
productos = [
    Producto(
        product_id=i,
        category_id=random.randint(1, 100),
        category_code=f"categoria_{random.randint(1, 100)}",
        brand=f"marca_{random.randint(1, 50)}",
        price=round(random.uniform(1, 2000), 2),
    )
    for i in range(1, N + 1)
]

# Preparamos los vectores para KNN por fuerza bruta.
ids = [p.product_id for p in productos]
puntos = [vectorizar(p) for p in productos]

# 1. Construcción del KD-Tree.
indice = IndiceKD()

inicio = time.perf_counter()
indice.construir(productos)
tiempo_construccion = time.perf_counter() - inicio

# Elegimos un producto como consulta.
producto_consulta = productos[500]
consulta = vectorizar(producto_consulta)

# 2. Consulta mediante KD-Tree.
inicio = time.perf_counter()
resultado_kd = indice.arbol.knn(consulta, K + 1)
tiempo_kd = time.perf_counter() - inicio

# Excluimos el propio producto consultado.
resultado_kd = [
    (distancia, product_id)
    for distancia, product_id in resultado_kd
    if product_id != producto_consulta.product_id
][:K]

nodos_visitados = indice.arbol.nodos_visitados

# 3. Consulta por fuerza bruta.
inicio = time.perf_counter()
resultado_exacto = knn_exacto(puntos, ids, consulta, K + 1)
tiempo_exacto = time.perf_counter() - inicio

resultado_exacto = [
    (distancia, product_id)
    for distancia, product_id in resultado_exacto
    if product_id != producto_consulta.product_id
][:K]

# 4. Resultados.
print("=" * 55)
print("PRUEBA DE VOLUMEN: KD-TREE VS KNN EXACTO")
print("=" * 55)
print(f"Productos: {N:,}")
print(f"K: {K}")
print(f"Producto consultado: {producto_consulta.product_id}")

print(f"\nConstrucción KD-Tree: {tiempo_construccion:.6f} segundos")
print(f"Consulta KD-Tree:     {tiempo_kd:.6f} segundos")
print(f"Consulta fuerza bruta:{tiempo_exacto:.6f} segundos")
print(f"Nodos visitados:      {nodos_visitados:,} de {N:,}")

print("\nVecinos KD-Tree:")
print([product_id for _, product_id in resultado_kd])

print("\nVecinos fuerza bruta:")
print([product_id for _, product_id in resultado_exacto])

print("\n¿Coinciden exactamente?:", resultado_kd == resultado_exacto)

if tiempo_kd > 0:
    print(f"Factor de velocidad: {tiempo_exacto / tiempo_kd:.2f}x")