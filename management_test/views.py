# views.py
import os
import json
import random
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from .models import ResultadoTest
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from .models import PreguntaRespondida
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from .models import ResultadoInteligencia
from django.contrib.auth.decorators import login_required
import json
from django.db.models import Q
from django.utils.timezone import now
import json



def home(request):
    test_dir = os.path.join(settings.BASE_DIR, 'test')
    tests = []

    for filename in os.listdir(test_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tests.append({
                    'title': data.get('title', 'Sin título'),
                    'description': data.get('description', ''),
                    'filename': filename,
                })

    return render(request, 'management_test/tests.html', {'tests': tests})


def realizar_test(request, filename):
    if not filename:
        return redirect('test')  # Redirige a la página de listado si no hay archivo

    test_path = os.path.join(settings.BASE_DIR, 'test', filename)

    try:
        with open(test_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
    except FileNotFoundError:
        return HttpResponse("Archivo no encontrado", status=404)
    except json.JSONDecodeError:
        return HttpResponse("Error al procesar el JSON", status=400)

    all_questions = test_data.get('questions', [])
    total_available = len(all_questions)

    if 'indices' not in request.session or 'respuestas' not in request.session:
        cantidad = min(20, total_available)
        indices = random.sample(range(total_available), cantidad)
        request.session['indices'] = indices
        request.session['respuestas'] = {}
        request.session['filename'] = filename
        request.session.modified = True

    indices = request.session['indices']
    total = len(indices)
    actual_index = int(request.GET.get('pregunta', 0))

    if request.method == 'POST':
        respuestas_usuario = request.POST.getlist('respuesta')
        request.session['respuestas'][str(actual_index)] = respuestas_usuario
        request.session.modified = True

        if actual_index + 1 < total:
            return HttpResponseRedirect(f"{request.path}?pregunta={actual_index + 1}")
        else:
            request.session['current_test'] = filename
            return redirect('resultado_test')

    index_pregunta = indices[actual_index]
    pregunta = all_questions[index_pregunta]

    barra_estado = []
    for idx, preg_idx in enumerate(indices):
        seleccion = request.session['respuestas'].get(str(idx), [])
        estado = 'respondida' if seleccion else 'no_respondida'
        barra_estado.append({
            'numero': idx + 1,
            'estado': estado,
            'actual': (idx == actual_index),
        })

    context = {
        'pregunta': pregunta,
        'numero': actual_index + 1,
        'total': total,
        'barra_estado': barra_estado,
        'test': {
            'title': test_data.get('title', ''),
            'description': test_data.get('description', ''),
            'filename': filename,
        }
    }

    return render(request, 'management_test/realizar_test.html', context)


def resultado_test(request):
    respuestas = request.session.get('respuestas', {})
    indices = request.session.get('indices', [])
    filename = request.session.get('filename', None)

    if not filename:
        return HttpResponse("No hay test cargado.", status=400)

    test_path = os.path.join(settings.BASE_DIR, 'test', filename)
    with open(test_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    all_questions = test_data.get('questions', [])
    resultados = []
    total_correctas = 0
    tipo_test = 'clasico'  # por defecto

    es_inteligencias = 'inteligencias' in filename.lower()
    puntajes = {}

    for i, index in enumerate(indices):
        pregunta = all_questions[index]
        opciones = pregunta.get('options', [])
        correctas = sorted([op['text'] for op in opciones if op.get('ok')])
        seleccionadas = respuestas.get(str(i), [])
        if isinstance(seleccionadas, str):
            seleccionadas = [seleccionadas]
        seleccionadas = sorted(seleccionadas)

        es_correcta = seleccionadas == correctas
        if es_correcta:
            total_correctas += 1

        item = {
            'pregunta': pregunta['question'],
            'seleccionadas': seleccionadas,
            'correctas': correctas,
            'es_correcta': es_correcta
        }

        if es_inteligencias:
            tipo_test = 'inteligencias'
            inteligencia = pregunta.get('inteligencia', 'Sin categoría')
            item['inteligencia'] = inteligencia
            puntajes[inteligencia] = puntajes.get(inteligencia, 0) + 1 if es_correcta else puntajes.get(inteligencia, 0)

        resultados.append(item)

    predominante = max(puntajes, key=puntajes.get) if es_inteligencias and puntajes else None

    # ✅ Guardar en base de datos
    if request.user.is_authenticated:
        resultado_db = ResultadoTest.objects.create(
            user=request.user,
            test_title=test_data.get('title', 'Sin título'),
            filename=filename,
            fecha=now(),
            total_preguntas=len(indices),
            aciertos=total_correctas,
            fallos=len(indices) - total_correctas,
            detalle=resultados  # asumiendo que este campo acepta JSON (como JSONField)
        )

        for r in resultados:
            PreguntaRespondida.objects.create(
                resultado=resultado_db,
                user=request.user,
                pregunta=r['pregunta'],
                seleccionadas=r['seleccionadas'],
                correctas=r['correctas'],
                es_correcta=r['es_correcta']
            )

    # ✅ Limpiar sesión para repetir test
    for key in ['respuestas', 'indices', 'filename']:
        request.session.pop(key, None)

    # ✅ Contexto para la plantilla
    if es_inteligencias:
        context = {
            'tipo_test': 'inteligencias',
            'resultados': puntajes,
            'predominante': predominante,
            'aciertos': total_correctas,
            'total': len(indices),
        }
    else:
        context = {
            'tipo_test': 'clasico',
            'resultados': resultados,
            'aciertos': total_correctas,
            'fallos': len(indices) - total_correctas,
            'total': len(indices),
        }

    return render(request, 'management_test/resultado.html', context)


@login_required
def historial_tests(request):
    titulo_query = request.GET.get('titulo', '')

    resultados = ResultadoTest.objects.filter(user=request.user)
    titulos_unicos = resultados.values_list('test_title', flat=True).distinct()

    if titulo_query:
        resultados = resultados.filter(test_title__icontains=titulo_query)

    return render(request, 'management_test/historial.html', {
        'resultados': resultados,
        'titulos_unicos': titulos_unicos,
    })

@login_required
def dashboard_usuario(request):
    resultados = ResultadoTest.objects.filter(user=request.user)
    total_tests = resultados.count()
    promedio_aciertos = resultados.aggregate(prom=Avg('aciertos'))['prom']
    promedio_fallos = resultados.aggregate(prom=Avg('fallos'))['prom']
    test_por_data = resultados.order_by('-fecha')
    
    context = {
        'total_tests': total_tests,
        'promedio_aciertos': promedio_aciertos or 0,
        'promedio_fallos': promedio_fallos or 0,
        'test_por_data': test_por_data or 0,
    }

    return render(request, 'management_test/dashboard_usuario.html', context)

@login_required
def detalle_resultado_test(request, test_id):
    resultado = get_object_or_404(ResultadoTest, id=test_id, user=request.user)
    detalle_json = resultado.detalle  # campo tipo JSONField
    resultados = []
    datos_grafico = []

    puntajes = {}  # Para inteligencias múltiples
    
    for item in detalle_json:
        es_correcta = set(item['seleccionadas']) == set(item['correctas'])

        resultados.append({
            'pregunta': item['pregunta'],
            'seleccionadas': item['seleccionadas'],
            'correctas': item['correctas'],
            'es_correcta': es_correcta,
        })
        datos_grafico = resultados

        # Contar puntuación por inteligencia si aplica
        inteligencia = item.get('inteligencia')
        if inteligencia:
            puntajes[inteligencia] = puntajes.get(inteligencia, 0) + (1 if es_correcta else 0)
    
    context = {
        'resultado': resultado,
        'aciertos': resultado.aciertos,
        'total': resultado.aciertos + resultado.fallos,
        'resultados': resultados,
        'datos_grafico': datos_grafico,      # esto es un dict tipo {'Visual': 5, 'Musical': 3, ...}
    }
    
    # Solo si es test de inteligencias múltiples y hay puntajes, serializamos a JSON
    if resultado.test_title.lower() == "inteligencias múltiples" and puntajes:
        predominante = max(puntajes, key=puntajes.get)
        context.update({
            'grafico_datos': json.dumps(puntajes),  # <-- Aquí serializamos JSON
            'predominante': predominante,
        })

    return render(request, 'management_test/detalle_test.html', context)

INTELIGENCIAS = [
    "Lingüística", "Lógico-Matemática", "Corporal-Kinestésica", "Musical",
    "Interpersonal", "Intrapersonal", "Naturalista", "Espacial"
]

# Mapeo: pregunta_id -> tipo inteligencia
MAPEO_INTELIGENCIA = {
    1: "Lingüística", 2: "Lógico-Matemática", 3: "Corporal-Kinestésica",
    # … continúa hasta 100
}

@login_required
def evaluar_test(request):
    if request.method == 'POST':
        respuestas = request.POST  # {'p1': '3', 'p2': '5', ...}
        totales = {intel: 0 for intel in INTELIGENCIAS}

        for clave, valor in respuestas.items():
            if clave.startswith('p'):
                id_pregunta = int(clave[1:])
                intel = MAPEO_INTELIGENCIA.get(id_pregunta)
                if intel:
                    totales[intel] += int(valor)

        # Guardar resultado
        resultado = ResultadoInteligencia.objects.create(
            usuario=request.user,
            resultados=totales
        )

        return render(request, 'tests/resultados.html', {
            'resultados': totales,
            'predominante': resultado.inteligencia_predominante()
        })

    return redirect('tests:test')  # Redirige si entran por GET