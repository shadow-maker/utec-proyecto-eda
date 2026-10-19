from pipeline_eda.etapa5_kdtree import KDTree, knn_exacto

puntos = [
    (1.0, 10.0),
    (1.1, 10.0),
    (3.0, 20.0),
    (1.2, 10.0),
    (4.0, 30.0),
]

ids = [101, 102, 103, 104, 105]
consulta = (1.0, 10.0)

arbol = KDTree()
arbol.construir(puntos, ids)

resultado_arbol = arbol.knn(consulta, 3)
resultado_exacto = knn_exacto(puntos, ids, consulta, 3)

print("KNN KD-Tree:", resultado_arbol)
print("KNN fuerza bruta:", resultado_exacto)
print("¿Coinciden?:", resultado_arbol == resultado_exacto)
print("Profundidad:", arbol.profundidad)
print("Nodos visitados:", arbol.nodos_visitados)

print(
    "Rango:",
    arbol.rango((0.9, 9.0), (1.2, 10.0))
)