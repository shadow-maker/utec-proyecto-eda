
from pipeline_eda.etapa7_similitud import HNSW
from pipeline_eda.etapa5_kdtree import knn_exacto

print("=== PRUEBA HNSW VS KNN EXACTO ===")

# Precio normalizado y categoría.
productos = {
    1: (0.10, 100),
    2: (0.12, 100),
    3: (0.15, 100),
    4: (0.70, 200),
    5: (0.75, 200),
    6: (0.90, 300),
    7: (0.11, 100),
    8: (0.72, 200),
}

hnsw = HNSW(m=4, ef_construccion=20, seed=42)

for producto_id, vector in productos.items():
    hnsw.insertar(producto_id, vector)

print("Productos indexados:", len(hnsw.vectores))
print("Nivel máximo:", hnsw.nivel_maximo)

# Consultamos productos similares al producto 1.
consulta = productos[1]
k = 3

# Excluimos el propio producto de ambas comparaciones.
exactos = knn_exacto(
    [v for id_, v in productos.items() if id_ != 1],
    [id_ for id_ in productos if id_ != 1],
    consulta,
    k
)

aproximados = [
    (distancia, id_)
    for distancia, id_ in hnsw.buscar(
        consulta, k + 1, ef=20
    )
    if id_ != 1
][:k]

print("\nKNN EXACTO:")
print(exactos)

print("\nHNSW:")
print(aproximados)

ids_exactos = {id_ for _, id_ in exactos}
ids_hnsw = {id_ for _, id_ in aproximados}

recall = len(ids_exactos & ids_hnsw) / len(ids_exactos)

print(f"\nRecall@{k}: {recall:.2%}")
print("Nodos visitados:", hnsw.nodos_visitados)

assert len(aproximados) == k
assert recall == 1.0

print("\nPRUEBA HNSW COMPLETADA")
