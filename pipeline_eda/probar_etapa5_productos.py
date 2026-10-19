
from pipeline_eda.evento import Producto
from pipeline_eda.etapa5_kdtree import IndiceKD

productos = [
    Producto(101, 10, "ropa", "MarcaA", 100.0),
    Producto(102, 10, "ropa", "MarcaB", 105.0),
    Producto(103, 10, "ropa", "MarcaC", 110.0),
    Producto(104, 20, "electronica", "MarcaD", 500.0),
    Producto(105, 20, "electronica", "MarcaE", 520.0),
    Producto(106, 30, "hogar", "MarcaF", 80.0),
]

indice = IndiceKD()
indice.construir(productos)

print("=== PRODUCTOS SIMILARES ===")
for product_id in [101, 104, 106]:
    similares = indice.similares(product_id, 2)
    print(f"Producto {product_id} -> similares: {similares}")

print("\n=== PRODUCTO INEXISTENTE ===")
print("Resultado:", indice.similares(999, 2))
print("Esperado: []")

print("\n=== MÉTRICAS DEL ÍNDICE ===")
print(indice.metricas())
