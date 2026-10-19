
from pipeline_eda.etapa5_kdtree import KDTree, knn_exacto

print("=== PRUEBA 1: ÁRBOL VACÍO ===")
arbol = KDTree()
print("Resultado:", arbol.knn((1.0, 2.0), 3))
print("Esperado: []")

print("\n=== PRUEBA 2: K CERO ===")
print("Resultado:", arbol.knn((1.0, 2.0), 0))
print("Esperado: []")

print("\n=== PRUEBA 3: K NEGATIVO ===")
print("Resultado:", arbol.knn((1.0, 2.0), -1))
print("Esperado: []")

print("\n=== PRUEBA 4: K MAYOR QUE EL CATÁLOGO ===")
puntos = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
ids = [101, 102, 103]

arbol.construir(puntos, ids)
print("Resultado:", arbol.knn((1.0, 1.0), 10))
print("Esperado: los 3 productos")

print("\n=== PRUEBA 5: DIMENSIÓN INCORRECTA ===")
try:
    arbol.knn((1.0,), 2)
except ValueError as error:
    print("Error controlado:", error)
