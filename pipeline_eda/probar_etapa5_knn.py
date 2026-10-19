from pipeline_eda.etapa5_kdtree import knn_exacto

puntos = [
    (1.0, 10.0),
    (1.1, 10.0),
    (3.0, 20.0),
]

ids = [101, 102, 103]
consulta = (1.0, 10.0)

resultado = knn_exacto(puntos, ids, consulta, k=2)

print("Resultado KNN:", resultado)