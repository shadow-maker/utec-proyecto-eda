
import random
import time
import tracemalloc
from bisect import bisect_left, bisect_right, insort

from pipeline_eda.etapa4_bplustree import BPlusTree

N = 500000
NUM_CONSULTAS = 1000
random.seed(42)

# Mismos datos y mismo orden de inserción para ambas estructuras
datos = list(range(1, N + 1))
random.shuffle(datos)

consultas = random.sample(range(1, N + 1), NUM_CONSULTAS)
rangos = [(x, x + 20) for x in consultas[:100]]


def medir_memoria_y_construccion(construir):
    tracemalloc.start()
    inicio = time.perf_counter()

    estructura = construir()

    tiempo = time.perf_counter() - inicio
    _, memoria_pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return estructura, tiempo, memoria_pico / (1024 * 1024)


# A. B+ Tree
def construir_bplus():
    arbol = BPlusTree(orden=64)
    for clave in datos:
        arbol.insertar(clave, clave)
    return arbol


arbol, tiempo_bplus, memoria_bplus = medir_memoria_y_construccion(
    construir_bplus
)


# B. Lista ordenada
def construir_lista():
    lista = []
    for clave in datos:
        insort(lista, (clave, clave))
    return lista


lista, tiempo_lista, memoria_lista = medir_memoria_y_construccion(
    construir_lista
)


# Búsqueda exacta
inicio = time.perf_counter()
for clave in consultas:
    resultado = arbol.rango(clave, clave)
tiempo_busqueda_bplus = time.perf_counter() - inicio

inicio = time.perf_counter()
for clave in consultas:
    izquierda = bisect_left(lista, (clave, -float("inf")))
    derecha = bisect_right(lista, (clave, float("inf")))
    resultado = lista[izquierda:derecha]
tiempo_busqueda_lista = time.perf_counter() - inicio


# Consulta por rango
inicio = time.perf_counter()
for desde, hasta in rangos:
    resultado = arbol.rango(desde, hasta)
tiempo_rango_bplus = time.perf_counter() - inicio

inicio = time.perf_counter()
for desde, hasta in rangos:
    izquierda = bisect_left(lista, (desde, -float("inf")))
    derecha = bisect_right(lista, (hasta, float("inf")))
    resultado = lista[izquierda:derecha]
tiempo_rango_lista = time.perf_counter() - inicio


# Resultados
print(f"REGISTROS: {N:,}")
print(f"CONSULTAS EXACTAS: {NUM_CONSULTAS:,}")
print(f"CONSULTAS POR RANGO: {len(rangos)}")

print("\n--- CONSTRUCCIÓN ---")
print(f"B+ Tree: {tiempo_bplus:.4f} s")
print(f"Lista ordenada: {tiempo_lista:.4f} s")

print("\n--- BÚSQUEDA EXACTA ---")
print(f"B+ Tree: {tiempo_busqueda_bplus:.4f} s")
print(f"Lista ordenada: {tiempo_busqueda_lista:.4f} s")

print("\n--- CONSULTA POR RANGO ---")
print(f"B+ Tree: {tiempo_rango_bplus:.4f} s")
print(f"Lista ordenada: {tiempo_rango_lista:.4f} s")

print("\n--- MEMORIA PICO DURANTE CONSTRUCCIÓN ---")
print(f"B+ Tree: {memoria_bplus:.2f} MB")
print(f"Lista ordenada: {memoria_lista:.2f} MB")
