"""Pruebas integrales de etapa 5: Min-Max, categoría, exactitud y rendimiento.

Ejecutar desde la RAÍZ del repositorio:
    python -m pipeline_eda.probar_etapa5_comparativos

Para probar solo un volumen:
    python -m pipeline_eda.probar_etapa5_comparativos 10000

Para probar todos:
    python -m pipeline_eda.probar_etapa5_comparativos 10000 100000 500000

No modifica los archivos del proyecto ni requiere librerías externas.
"""
from __future__ import annotations

import math
import random
import statistics
import sys
import time
from dataclasses import dataclass

from .etapa5_kdtree import IndiceKD, KDTree, distancia_mixta, knn_exacto, vectorizar


@dataclass
class ProductoPrueba:
    """Solo los campos que utiliza la etapa 5."""
    product_id: int
    category_id: int
    price: float


CAT_A = 2103807459595380000
CAT_B = 2053013552326770000
CAT_C = 2053013559792630000
CAT_D = 2053013558920210000


def segundos(funcion):
    inicio = time.perf_counter()
    resultado = funcion()
    return resultado, time.perf_counter() - inicio


def tabla(encabezados, filas):
    valores = [[str(x) for x in fila] for fila in [encabezados, *filas]]
    anchos = [max(len(fila[i]) for fila in valores) for i in range(len(encabezados))]
    for numero, fila in enumerate(valores):
        print(" | ".join(valor.ljust(anchos[i]) for i, valor in enumerate(fila)))
        if numero == 0:
            print("-+-".join("-" * ancho for ancho in anchos))


def pruebas_controladas():
    print("\n" + "=" * 75)
    print("PRUEBA 1. NORMALIZACIÓN, CATEGORÍAS Y DISTANCIAS")
    print("=" * 75)

    productos = [
        ProductoPrueba(1, CAT_A, 0.79),
        ProductoPrueba(2, CAT_A, 10.00),
        ProductoPrueba(3, CAT_A, 35.79),
        ProductoPrueba(4, CAT_A, 251.74),  # Consulta
        ProductoPrueba(5, CAT_A, 275.00),
        ProductoPrueba(6, CAT_B, 33.20),
        ProductoPrueba(7, CAT_C, 543.10),
        ProductoPrueba(8, CAT_D, 3000.00),
    ]

    indice = IndiceKD()
    indice.construir(productos)
    assert indice.precio_min == 0.79
    assert indice.precio_max == 3000.00
    assert len(indice.ids) == len(productos)

    por_id = dict(zip(indice.ids, indice.puntos))
    tabla(
        ["ID", "Precio S/", "Precio normalizado", "Categoría"],
        [
            (p.product_id, f"{p.price:.2f}", f"{por_id[p.product_id][0]:.6f}",
             str(p.category_id))
            for p in productos
        ],
    )

    consulta_id = 4
    q = por_id[consulta_id]
    comparaciones = []
    for p in productos:
        if p.product_id == consulta_id:
            continue
        punto = por_id[p.product_id]
        comparaciones.append((
            p.product_id,
            "IGUAL (0)" if punto[1] == q[1] else "DISTINTA (1)",
            abs(punto[0] - q[0]),
            distancia_mixta(punto, q),
        ))
    comparaciones.sort(key=lambda x: (x[3], x[0]))
    print("\nDistancias respecto al producto 4 (S/ 251.74):")
    tabla(
        ["ID", "Categoría", "Diferencia precio norm.", "Distancia final"],
        [(pid, cat, f"{dif:.6f}", f"{dist:.6f}")
         for pid, cat, dif, dist in comparaciones],
    )

    # KNN exacto y KD-Tree incluyen al producto consultado: se elimina después.
    k = 5
    esperado = [
        pid for _, pid in knn_exacto(indice.puntos, indice.ids, q, k + 1)
        if pid != consulta_id
    ][:k]
    obtenido = indice.similares(consulta_id, k)
    assert obtenido == esperado, f"KD={obtenido}, exacto={esperado}"
    assert por_id[1][0] == 0.0 and por_id[8][0] == 1.0
    assert por_id[4][1] == CAT_A  # ID grande, sin pérdida de precisión
    assert distancia_mixta(por_id[4], por_id[5]) < 1
    assert distancia_mixta(por_id[4], por_id[6]) >= 1
    print(f"\nKNN exacto (k={k}): {esperado}")
    print(f"KD-Tree   (k={k}): {obtenido}")
    print("RESULTADO: CORRECTO (coincidencia exacta).")

    print("\n" + "=" * 75)
    print("PRUEBA 2. CASOS LÍMITE")
    print("=" * 75)
    iguales = [ProductoPrueba(10, CAT_A, 100), ProductoPrueba(11, CAT_B, 100)]
    indice_iguales = IndiceKD()
    indice_iguales.construir(iguales)
    assert all(p[0] == 0 for p in indice_iguales.puntos)
    assert indice_iguales.similares(10, 1) == [11]
    assert indice.similares(999999, 3) == []
    assert indice.similares(4, 0) == []
    assert indice.similares(4, 50) == [x[0] for x in comparaciones]
    assert len(indice.arbol.rango((0.0, CAT_A), (1.0, CAT_A))) == 5
    try:
        vectorizar(ProductoPrueba(99, CAT_A, -1), 0, 3000)
        raise AssertionError("Un precio negativo debería producir ValueError")
    except ValueError:
        pass
    print("Precios idénticos, k=0, ID inexistente, k grande, rango por categoría")
    print("y precio negativo: CORRECTO.")


def generar_productos(n: int, semilla: int = 2026):
    """Muestra reproducible con rango 0.79–3000 y categorías reales tipo ID."""
    rng = random.Random(semilla)
    categorias = [CAT_A, CAT_B, CAT_C, CAT_D]
    productos = [
        ProductoPrueba(1, CAT_A, 0.79),
        ProductoPrueba(2, CAT_B, 3000.0),
    ]
    for pid in range(3, n + 1):
        # Muchos productos baratos y algunos caros: precios no uniformes.
        precio = round(0.79 + (rng.random() ** 2) * (3000 - 0.79), 2)
        categoria = categorias[rng.randrange(len(categorias))]
        productos.append(ProductoPrueba(pid, categoria, precio))
    return productos


def benchmark(n: int, consultas: int = 5, k: int = 10):
    print(f"\n{'=' * 75}")
    print(f"PRUEBA DE VOLUMEN: {n:,} PRODUCTOS".replace(",", " "))
    print("=" * 75)

    productos, t_generar = segundos(lambda: generar_productos(n))
    indice = IndiceKD()
    _, t_construir = segundos(lambda: indice.construir(productos))

    # Consultas reproducibles, sin incluir el propio producto en el resultado.
    rng = random.Random(9876)
    elegidos = rng.sample(indice.ids, min(consultas, n))
    por_id = dict(zip(indice.ids, indice.puntos))
    tiempos_kd, tiempos_exacto, nodos = [], [], []
    resultados = []

    for consulta_id in elegidos:
        q = por_id[consulta_id]
        # Pedimos k+1 para excluir el producto de consulta de ambos métodos.
        kd_raw, t_kd = segundos(lambda: indice.arbol.knn(q, k + 1))
        visitados = indice.arbol.nodos_visitados
        exacto_raw, t_exacto = segundos(
            lambda: knn_exacto(indice.puntos, indice.ids, q, k + 1)
        )
        kd = [pid for _, pid in kd_raw if pid != consulta_id][:k]
        exacto = [pid for _, pid in exacto_raw if pid != consulta_id][:k]
        coincide = kd == exacto
        assert coincide, (
            f"FALLO n={n}, consulta={consulta_id}: KD={kd}, exacto={exacto}"
        )
        tiempos_kd.append(t_kd)
        tiempos_exacto.append(t_exacto)
        nodos.append(visitados)
        resultados.append((
            consulta_id, f"{t_kd * 1000:.3f}", f"{t_exacto * 1000:.3f}",
            visitados, "SÍ" if coincide else "NO",
        ))

    tabla(
        ["ID consulta", "KD-Tree (ms)", "Exacto (ms)", "Nodos visitados", "¿Iguales?"],
        resultados,
    )
    med_kd = statistics.median(tiempos_kd)
    med_ex = statistics.median(tiempos_exacto)
    aceleracion = med_ex / med_kd if med_kd > 0 else float("inf")
    resumen = {
        "n": n,
        "generacion_s": t_generar,
        "construccion_s": t_construir,
        "profundidad": indice.arbol.profundidad,
        "kd_ms": med_kd * 1000,
        "exacto_ms": med_ex * 1000,
        "aceleracion": aceleracion,
        "nodos": statistics.median(nodos),
        "coincidencias": len(resultados),
    }
    print(
        f"\nConstrucción: {t_construir:.4f} s | "
        f"Profundidad: {indice.arbol.profundidad} | "
        f"Precio mín/máx: S/ {indice.precio_min:.2f} / {indice.precio_max:.2f}"
    )
    print(
        f"Medianas: KD-Tree={resumen['kd_ms']:.3f} ms | "
        f"Exacto={resumen['exacto_ms']:.3f} ms | "
        f"Aceleración={aceleracion:.2f}x"
    )
    print(
        f"Nodos visitados (mediana): {resumen['nodos']:.0f} de {n} | "
        f"Coincidencias: {len(resultados)}/{len(resultados)}"
    )
    return resumen


def main():
    tamanos = [10_000, 100_000, 500_000]
    if len(sys.argv) > 1:
        try:
            tamanos = [int(x) for x in sys.argv[1:]]
        except ValueError:
            raise SystemExit("Usa tamaños enteros, ej.: 10000 100000")
        if any(n < 2 for n in tamanos):
            raise SystemExit("Cada tamaño debe ser >= 2")

    pruebas_controladas()
    resumenes = [benchmark(n) for n in tamanos]

    print("\n" + "=" * 75)
    print("CUADRO COMPARATIVO FINAL — ETAPA 5")
    print("=" * 75)
    tabla(
        ["Indicador"] + [f"{r['n']:,}".replace(",", " ") for r in resumenes],
        [
            ["Construcción KD (s)"] + [f"{r['construccion_s']:.4f}" for r in resumenes],
            ["Profundidad KD"] + [r["profundidad"] for r in resumenes],
            ["Consulta KD mediana (ms)"] + [f"{r['kd_ms']:.4f}" for r in resumenes],
            ["Consulta exacta mediana (ms)"] + [f"{r['exacto_ms']:.4f}" for r in resumenes],
            ["Aceleración exacto/KD"] + [f"{r['aceleracion']:.2f}x" for r in resumenes],
            ["Nodos KD visitados (mediana)"] + [f"{r['nodos']:.0f}" for r in resumenes],
            ["Consultas idénticas"] + [f"{r['coincidencias']}/{r['coincidencias']}" for r in resumenes],
        ],
    )
    print("\nNOTA: datos sintéticos reproducibles; resultados dependen del equipo.")
    print("La generación de datos no se incluye en el tiempo de construcción.")
    print("La comparación mide consultas individuales con k=10 y 5 consultas por tamaño.")


if __name__ == "__main__":
    main()

