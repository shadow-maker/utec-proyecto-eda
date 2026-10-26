
import random

from pipeline_eda.etapa5_kdtree import KDTree, knn_exacto

random.seed(42)

N = 1000
NUM_CONSULTAS = 100
K = 10

puntos = [
    (random.uniform(0, 100), random.uniform(0, 100))
    for _ in range(N)
]
ids = list(range(1, N + 1))

arbol = KDTree()
arbol.construir(puntos, ids)

errores = 0

for numero in range(NUM_CONSULTAS):
    consulta = (
        random.uniform(0, 100),
        random.uniform(0, 100),
    )

    resultado_kd = arbol.knn(consulta, K)
    resultado_exacto = knn_exacto(puntos, ids, consulta, K)

    if resultado_kd != resultado_exacto:
        errores += 1
        print(f"Diferencia en consulta {numero + 1}")

print("\n=== RESULTADO ===")
print("Consultas realizadas:", NUM_CONSULTAS)
print("Diferencias:", errores)
print("¿Todas coinciden?:", errores == 0)
