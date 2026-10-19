
# Resumen de rendimiento: B+ Tree vs. lista ordenada + bisect

resultados = [
    {
        "registros": 10_000,
        "bplus_construccion": 0.0352,
        "lista_construccion": 0.0204,
        "bplus_busqueda": 0.0003,
        "lista_busqueda": 0.0025,
        "bplus_rango": 0.0001,
        "lista_rango": 0.0003,
        "bplus_memoria": 0.85,
        "lista_memoria": 0.69,
    },
    {
        "registros": 100_000,
        "bplus_construccion": 0.5768,
        "lista_construccion": 1.9022,
        "bplus_busqueda": 0.0002,
        "lista_busqueda": 0.0038,
        "bplus_rango": 0.0000,
        "lista_rango": 0.0003,
        "bplus_memoria": 8.46,
        "lista_memoria": 6.87,
    },
    {
        "registros": 500_000,
        "bplus_construccion": 8.9155,
        "lista_construccion": 53.6623,
        "bplus_busqueda": 0.0003,
        "lista_busqueda": 0.0057,
        "bplus_rango": 0.0001,
        "lista_rango": 0.0006,
        "bplus_memoria": 42.31,
        "lista_memoria": 34.49,
    },
]

print("=" * 100)
print("COMPARACIÓN DE RENDIMIENTO: B+ TREE VS. LISTA ORDENADA")
print("=" * 100)

for r in resultados:
    print(f"\nREGISTROS: {r['registros']:,}")
    print("-" * 85)
    print(
        f"{'Indicador':<25}{'B+ Tree':>15}"
        f"{'Lista + bisect':>20}{'Ganador':>20}"
    )

    comparaciones = [
        ("Construcción (s)", "bplus_construccion", "lista_construccion"),
        ("Búsqueda exacta (s)", "bplus_busqueda", "lista_busqueda"),
        ("Consulta por rango (s)", "bplus_rango", "lista_rango"),
        ("Memoria pico (MB)", "bplus_memoria", "lista_memoria"),
    ]

    for nombre, clave_b, clave_l in comparaciones:
        b = r[clave_b]
        l = r[clave_l]

        if b < l:
            ganador = "B+ Tree"
        elif l < b:
            ganador = "Lista"
        else:
            ganador = "Empate"

        print(f"{nombre:<25}{b:>15.4f}{l:>20.4f}{ganador:>20}")


print("\n" + "=" * 100)
print("FACTORES DE VELOCIDAD")
print("=" * 100)

for r in resultados:
    print(f"\n{r['registros']:,} registros:")

    for nombre, b_key, l_key in [
        ("Construcción", "bplus_construccion", "lista_construccion"),
        ("Búsqueda exacta", "bplus_busqueda", "lista_busqueda"),
        ("Consulta por rango", "bplus_rango", "lista_rango"),
    ]:
        b = r[b_key]
        l = r[l_key]

        if b > 0 and l > 0:
            if b < l:
                print(f"  {nombre}: B+ Tree {l / b:.2f}x más rápido")
            elif l < b:
                print(f"  {nombre}: Lista {b / l:.2f}x más rápida")
            else:
                print(f"  {nombre}: tiempos iguales")
        else:
            print(
                f"  {nombre}: no se calcula el factor "
                "porque un tiempo está redondeado a cero"
            )

print("\nNota: los tiempos son los medidos en tu computadora.")
print("La memoria corresponde al pico registrado por tracemalloc.")
