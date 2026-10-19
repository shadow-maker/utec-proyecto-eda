from pipeline_eda.evento import Event
from pipeline_eda.etapa4_bplustree import IndiceProductos
import time

indice = IndiceProductos(orden=64)

N = 10000

inicio = time.perf_counter()

for i in range(N):
    producto = (i % 1000) + 1
    precio = 10.0 + (i % 20)

    ev = Event(
        event_time=i,
        event_type="view",
        product_id=producto,
        category_id=1,
        category_code=None,
        brand=None,
        price=precio,
        user_id=100 + producto,
        user_session=f"sesion_{i}",
    )

    indice.consumir(ev)

fin = time.perf_counter()

print("EVENTOS PROCESADOS:", indice.metricas()["eventos_procesados"])
print("PRODUCTOS INDEXADOS:", indice.metricas()["productos_indexados"])
print("CLAVES ARBOL PRECIO:",
      indice.metricas()["arbol_precio"]["claves_indexadas"])
print("CLAVES ARBOL TIEMPO:",
      indice.metricas()["arbol_tiempo"]["claves_indexadas"])
print("ALTURA ARBOL PRECIO:",
      indice.metricas()["arbol_precio"]["altura"])
print("ALTURA ARBOL TIEMPO:",
      indice.metricas()["arbol_tiempo"]["altura"])
print("TIEMPO DE PROCESAMIENTO:", round(fin - inicio, 4), "segundos")
