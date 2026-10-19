
from pipeline_eda.etapa4_bplustree import BPlusTree

arbol = BPlusTree(orden=4)

# Insertar datos de prueba
arbol.insertar(10, "A")
arbol.insertar(20, "B")
arbol.insertar(30, "C")
arbol.insertar(20, "D")
arbol.insertar(40, "E")
arbol.insertar(50, "F")
arbol.insertar(60, "G")

# Probar búsqueda puntual
print("1. BUSQUEDA:")
print(arbol.buscar(20))

# Probar consulta por rango
print("\n2. CONSULTA POR RANGO:")
print(list(arbol.rango(20, 50)))

# Probar una clave inexistente
print("\n3. CLAVE INEXISTENTE:")
print(arbol.buscar(999))

# Probar métricas
print("\n4. METRICAS:")
print(arbol.metricas())

print("\n5. PRUEBA DE MUCHAS INSERCIONES:")

arbol_grande = BPlusTree(orden=4)

for numero in range(1, 101):
    arbol_grande.insertar(numero, f"producto_{numero}")

print("Búsqueda de 75:", arbol_grande.buscar(75))
print("Rango de 40 a 45:", list(arbol_grande.rango(40, 45)))
print("Métricas:", arbol_grande.metricas())

