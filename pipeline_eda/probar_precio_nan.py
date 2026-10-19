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
indice.consumir(crear_evento(200, 1, float("nan")))

print(
    "PRECIO 25:",
    indice.productos_en_rango_precio(25, 25)
)
print("MÉTRICAS:", indice.metricas())
