from pipeline_eda.etapa4_bplustree import BPlusTree

arbol = BPlusTree(orden=4)

# Insertar 10.000 claves, prueba con 10,000 datos
for numero in range(1, 10001):
    arbol.insertar(numero, f"producto_{numero}")

print("1. TOTAL DE CLAVES INDEXADAS:")
print(arbol.metricas()["claves_indexadas"])

print("\n2. BUSQUEDA DE CLAVE 7500:")
print(arbol.buscar(7500))

print("\n3. RANGO DE 5000 A 5005:")
print(list(arbol.rango(5000, 5005)))

print("\n4. METRICAS:")
print(arbol.metricas())