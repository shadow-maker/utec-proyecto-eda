
from pipeline_eda.etapa5_kdtree import KDTree, knn_exacto

print("=== PRUEBA 1: PRODUCTOS CON ATRIBUTOS IDÉNTICOS ===")

puntos = [
    (10.0, 1.0),
    (10.0, 1.0),
    (10.0, 1.0),
    (20.0, 2.0),
]
ids = [101, 102, 103, 104]

consulta = (10.0, 1.0)

arbol = KDTree()
arbol.construir(puntos, ids)

resultado_kd = arbol.knn(consulta, 3)
resultado_exacto = knn_exacto(puntos, ids, consulta, 3)

print("KD-Tree:", resultado_kd)
print("KNN exacto:", resultado_exacto)
print("¿Coinciden?:", resultado_kd == resultado_exacto)

print("\n=== PRUEBA 2: PRODUCTOS A LA MISMA DISTANCIA ===")

puntos = [
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (5.0, 5.0),
]
ids = [201, 202, 203, 204, 205]

consulta = (0.0, 0.0)

arbol.construir(puntos, ids)

resultado_kd = arbol.knn(consulta, 4)
resultado_exacto = knn_exacto(puntos, ids, consulta, 4)

print("KD-Tree:", resultado_kd)
print("KNN exacto:", resultado_exacto)
print("¿Coinciden?:", resultado_kd == resultado_exacto)

print("\n=== RESULTADO FINAL ===")

correcto = resultado_kd == resultado_exacto
print("La última prueba coincide:", correcto)
