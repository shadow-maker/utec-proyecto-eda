from pipeline_eda.evento import Event
from pipeline_eda.etapa4_bplustree import IndiceProductos

indice = IndiceProductos(orden=4)

def crear_evento(producto, precio):
    return Event(
        event_time=100,
        event_type="view",
        product_id=producto,
        category_id=1,
        category_code=None,
        brand=None,
        price=precio,
        user_id=100 + producto,
        user_session=f"sesion_{producto}",
    )

indice.consumir(crear_evento(1, 0.0))
indice.consumir(crear_evento(2, -5.0))
indice.consumir(crear_evento(3, 10.0))

print("PRODUCTO CON PRECIO CERO:", indice.productos_en_rango_precio(0, 0))
print("PRODUCTOS CON PRECIO NEGATIVO:", indice.productos_en_rango_precio(-10, -1))
print("PRODUCTOS CON PRECIO POSITIVO:", indice.productos_en_rango_precio(1, 20))
print("MÉTRICAS:", indice.metricas())

from pipeline_eda.evento import Event
from pipeline_eda.etapa4_bplustree import IndiceProductos

indice = IndiceProductos(orden=4)

def crear_evento(tiempo, producto, precio):
    return Event(
        event_time=tiempo,
        event_type="view",
        product_id=producto,
        category_id=1,
        category_code=None,
        brand=None,
        price=precio,
        user_id=100 + producto,
        user_session=f"sesion_{producto}",
    )

indice.consumir(crear_evento(100, 1, 25.0))
indice.consumir(crear_evento(200, 1, -5.0))

print("PRECIO VÁLIDO ANTES Y DESPUÉS:", indice.productos_en_rango_precio(25, 25))
print("PRECIO NEGATIVO:", indice.productos_en_rango_precio(-5, -5))
print("MÉTRICAS:", indice.metricas())

