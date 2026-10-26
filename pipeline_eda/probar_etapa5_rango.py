
from pipeline_eda.etapa5_kdtree import KDTree

puntos = [
    (10.0, 1.0),
    (20.0, 2.0),
    (30.0, 3.0),
    (40.0, 4.0),
    (50.0, 5.0),
]
ids = [101, 102, 103, 104, 105]

arbol = KDTree()
arbol.construir(puntos, ids)

resultado = arbol.rango(
    minimo=(20.0, 2.0),
    maximo=(40.0, 4.0),
)

print("=== BÚSQUEDA POR RANGO ===")
print("Productos encontrados:", resultado)
print("Esperado: [102, 103, 104]")
print("¿Correcto?:", resultado == [102, 103, 104])

print("\n=== RANGO SIN RESULTADOS ===")
resultado_vacio = arbol.rango(
    minimo=(100.0, 10.0),
    maximo=(200.0, 20.0),
)
print("Resultado:", resultado_vacio)
print("¿Correcto?:", resultado_vacio == [])
