
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


# 1. Insertar eventos
indice.consumir(crear_evento(100, 1, 10.0))
indice.consumir(crear_evento(200, 2, 20.0))
indice.consumir(crear_evento(300, 1, 15.0))
indice.consumir(crear_evento(300, 3, 15.0))

# 2. Consultar el precio actual de los productos
print("1. PRODUCTOS CON PRECIO ENTRE 15 Y 15:")
print(indice.productos_en_rango_precio(15.0, 15.0))

# 3. Verificar que el precio anterior ya no aparezca
print("\n2. PRODUCTOS CON EL PRECIO ANTIGUO DE 10:")
print(indice.productos_en_rango_precio(10.0, 10.0))

# 4. Consultar eventos por tiempo
print("\n3. EVENTOS ENTRE 200 Y 300:")
eventos = list(indice.eventos_en_rango_tiempo(200, 300))
print([
    (ev.event_time, ev.product_id, ev.price)
    for ev in eventos
])

# 5. Revisar métricas
print("\n4. METRICAS:")
print(indice.metricas())

# 5. Probar múltiples cambios de precio
indice.consumir(crear_evento(400, 1, 25.0))
indice.consumir(crear_evento(500, 1, 30.0))

print("\n5. PRECIO ACTUAL DEL PRODUCTO 1:")
print(indice.productos_en_rango_precio(30.0, 30.0))

print("\n6. VERIFICAR QUE YA NO TENGA PRECIO 25:")
print(indice.productos_en_rango_precio(25.0, 25.0))

print("\n7. VERIFICAR QUE YA NO TENGA PRECIO 15:")
print(indice.productos_en_rango_precio(15.0, 15.0))

print("\n8. HISTORIAL DEL PRODUCTO 1:")
eventos_producto_1 = [
    (ev.event_time, ev.product_id, ev.price)
    for ev in indice.eventos_en_rango_tiempo(100, 500)
    if ev.product_id == 1
]
print(eventos_producto_1)

print("\n9. METRICAS FINALES:")
print(indice.metricas())