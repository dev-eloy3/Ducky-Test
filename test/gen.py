import json

# Ruta de entrada y salida
input_file = "inteligencias_multiples_categorizado_final.json"
output_file = "inteligencias_multiples_limpio_20min_por_categoria.json"

# Cargar JSON
with open(input_file, "r", encoding="utf-8") as f:
    raw = json.load(f)

# Si el archivo está en formato objeto con "questions_by_category"
if isinstance(raw, dict) and "questions_by_category" in raw:
    data = raw["questions_by_category"]
else:
    raise ValueError("Estructura JSON no válida")

# Consolidar preguntas únicas y con mínimo 20 por categoría
preguntas_finales = []
id_actual = 1

for categoria, preguntas in sorted(data.items()):
    preguntas_unicas = {}
    for p in preguntas:
        texto = p.get("question", "").strip()
        if texto and texto not in preguntas_unicas:
            preguntas_unicas[texto] = p

    lista_filtrada = list(preguntas_unicas.values())
    if len(lista_filtrada) >= 20:
        for p in lista_filtrada:
            p["id"] = id_actual
            p["categoria"] = categoria
            preguntas_finales.append(p)
            id_actual += 1

# Guardar nuevo archivo JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(preguntas_finales, f, ensure_ascii=False, indent=2)

print(f"Archivo generado: {output_file} con {len(preguntas_finales)} preguntas.")
