from pipeline_eda.evento import Producto
from pipeline_eda.etapa5_kdtree import IndiceKD

productos = [
    Producto(101, 10, "ropa", "MarcaA", 100.0),
    Producto(102, 10, "ropa", "MarcaA", 110.0),
    Producto(103, 20, "electronica", "MarcaB", 500.0),
    Producto(104, 10, "ropa", "MarcaC", 120.0),
    Producto(105, 30, "hogar", "MarcaD", 800.0),
]

indice = IndiceKD()
indice.construir(productos)

print("PRODUCTOS SIMILARES A 101:")
print(indice.similares(101, 2))

print("\nPRODUCTOS SIMILARES A 103:")
print(indice.similares(103, 2))

print("\nPRODUCTO INEXISTENTE:")
print(indice.similares(999, 2))

print("\nMÉTRICAS:")
print(indice.metricas())