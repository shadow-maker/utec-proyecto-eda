from pipeline_eda.etapa4_bplustree import BPlusTree

arbol = BPlusTree(orden=4)

# Insertar claves desordenadas y una clave duplicada
datos = [
    (50, "A"),
    (20, "B"),
    (40, "C"),
    (10, "D"),
    (30, "E"),
    (20, "F"),
    (60, "G"),
]

for clave, valor in datos:
    arbol.insertar(clave, valor)

# Buscar la clave duplicada
print("1. BUSQUEDA DE CLAVE 20:")
print(arbol.buscar(20))

# Consultar el rango completo
print("\n2. CONSULTA POR RANGO:")
print(list(arbol.rango(10, 60)))

# Revisar métricas
print("\n3. METRICAS:")
print(arbol.metricas())

print("\n4. RANGO SIN RESULTADOS:")
print(list(arbol.rango(70, 90)))

print("\n5. RANGO INVERTIDO:")
print(list(arbol.rango(50, 20)))

print("\n6. RANGO DE UNA SOLA CLAVE:")
print(list(arbol.rango(20, 20)))

print("\n7. RANGO CON LIMITE EXISTENTE Y OTRO INEXISTENTE:")
print(list(arbol.rango(20, 35)))