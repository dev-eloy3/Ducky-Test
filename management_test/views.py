import json
import os
import random
from collections import Counter
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.shortcuts import reverse
from django.utils.timezone import now
from .form import ComentarioForm
from .models import PreguntaRespondida, ResultadoInteligencia, ResultadoTest, ComentariosProfessores
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import ResultadoTest, ComentariosProfessores

def es_profesor(user):
    return user.groups.filter(name='Teachers').exists()

def es_alumno(user):
    return user.groups.filter(name='alumnos').exists()

@login_required
@user_passes_test(es_profesor)
def comentario_professor(request, tests_id):
   test = get_object_or_404(ResultadoTest, id=tests_id)
   titulo = request.GET.get('titulo','')
   usuarios = request.GET.get('usuarios','')
   usuarios = usuarios.strip() if usuarios else None
   usuarios = usuarios if usuarios and usuarios not in ['', 'None', '+'] else ''

   if request.method == 'POST':
        form = ComentarioForm(request.POST)
        if form.is_valid():
                comentario = form.save(commit=False)
                comentario.professor = request.user
                comentario.test = test
                comentario.save()
                return redirect(f"{reverse('dashboard_professor')}?titulo={titulo}&usuarios={usuarios}")
   else:
        form = ComentarioForm()
        
   return render(request, 'management_test/formulario_professor.html', {'form': form, 'test': test})
   
User = get_user_model()

@login_required
@user_passes_test(es_profesor)
def profesor_vista(request):
    titulos = request.GET.get('titulo')
    usuarios = request.GET.get('usuarios') 
    usuarios = usuarios.strip() if usuarios else None
    usuarios = usuarios if usuarios and usuarios  not in ['', 'None', '+'] else None

    test = ResultadoTest.objects.count()
    test_usuarios = ResultadoTest.objects.select_related('user').order_by('-fecha')

    # Filtrar por título primero
    if titulos:
        test_usuarios = test_usuarios.filter(test_title=titulos)

    # Luego por usuario si está definido
    if usuarios:
        test_usuarios = test_usuarios.filter(user__username=usuarios)

    # Alumnos únicos con resultados
    nombres = User.objects.filter(resultadotest__isnull=False).distinct().values_list('username', flat=True)

    # Títulos únicos para el desplegable
    titulo_query = ResultadoTest.objects.all()
    
    if usuarios:
        titulo_query = titulo_query.filter(user__username=usuarios)
    todos_los_titulos = titulo_query.values_list('test_title', flat=True).distinct().order_by('test_title')

    # Comentarios asignados
    for resultado in test_usuarios:
        resultado.tiene_comentario = ComentariosProfessores.objects.filter(test=resultado).exists()

    datos = {
        'test': test,
        'test_usuarios': test_usuarios,
        'titulos': todos_los_titulos,
        'titulo_filtrado': titulos,
        'nombres': nombres,
        'usuarios': usuarios,
    }

    return render(request, 'management_test/dashboard_professor.html', datos)

@login_required
@user_passes_test(es_profesor)
def modificar_comentario(request, id):
    comentario = get_object_or_404(ComentariosProfessores, test_id=id)
    titulo = request.GET.get('titulo','')
    usuarios = request.GET.get('usuarios','')
    usuarios = usuarios.strip() if usuarios else None
    usuarios = usuarios if usuarios and usuarios not in ['', 'None', '+'] else ''
    
    if request.method == 'POST':
        form = ComentarioForm(request.POST, instance=comentario)
        if form.is_valid():
            form.save()
            return redirect(f"{reverse('dashboard_professor')}?titulo={titulo}&usuarios={usuarios}")
    else:
        form = ComentarioForm(instance=comentario)

    contexto = {
        'form': form,
        'comentario': comentario
    }
    return render(request, 'management_test/formulario_professor.html', contexto)

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

    # Detecta si el usuario está en el grupo "Teachers"
    es_teacher = request.user.groups.filter(name='Teachers').exists()

    return render(request, 'management_test/tests.html', {
        'tests': tests,
        'es_teacher': es_teacher,
    })

@login_required
@user_passes_test(es_profesor)
def modificar_test(request, filename):
    test_path = os.path.join(settings.BASE_DIR, 'test', filename)

    if not os.path.exists(test_path):
        # Puedes mostrar un mensaje de error si el archivo no existe
        return redirect('home')

    if request.method == 'POST':
        # Leer datos del formulario
        nuevo_titulo = request.POST.get('titulo')
        nueva_descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')
        subcategoria = request.POST.get('subcategoria')
        tags_raw = request.POST.get('tags')
        tags = [t.strip() for t in tags_raw.split(',') if t.strip()]

        # Procesar preguntas
        preguntas = []
        contador = 1
        while True:
            texto = request.POST.get(f'pregunta_{contador}')
            if not texto:
                break

            opciones = []
            opcion_index = 1
            while True:
                texto_opcion = request.POST.get(f'opcion_{contador}_{opcion_index}')
                if not texto_opcion:
                    break
                es_correcta = f'ok_{contador}_{opcion_index}' in request.POST
                opciones.append({
                    'text': texto_opcion,
                    'ok': es_correcta,
                })
                opcion_index += 1

            preguntas.append({
                'text': texto,
                'options': opciones,
            })
            contador += 1

        # Crear estructura y sobrescribir JSON
        nuevo_contenido = {
            'title': nuevo_titulo,
            'description': nueva_descripcion,
            'category': categoria,
            'subcategory': subcategoria,
            'tags': tags,
            'questions': preguntas,
        }

        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(nuevo_contenido, f, ensure_ascii=False, indent=2)

        return redirect('home')

    else:
        with open(test_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        return render(request, 'management_test/modificar_test.html', {
            'filename': filename,
            'test_data': datos,
        })

@login_required
@user_passes_test(es_profesor)
def modificar_test_inteligencias(request, filename):
    test_path = os.path.join(settings.BASE_DIR, 'test', filename)

    if not os.path.exists(test_path):
        return redirect('home')

    if request.method == 'POST':
        with open(test_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        # Actualizar metadatos
        datos['title'] = request.POST.get('titulo', datos.get('title', ''))
        datos['description'] = request.POST.get('descripcion', datos.get('description', ''))

        # Actualizar preguntas y opciones
        for pregunta in datos.get('questions', []):
            pid = str(pregunta['id'])

            pregunta['question'] = request.POST.get(f'pregunta_{pid}', pregunta['question'])
            pregunta['categoria'] = request.POST.get(f'categoria_{pid}', pregunta.get('categoria', ''))

            for i, opcion in enumerate(pregunta['options'], start=1):
                opcion['text'] = request.POST.get(f'opcion_{pid}_{i}', opcion['text'])
                opcion['ok'] = f'ok_{pid}_{i}' in request.POST

        with open(test_path, 'w', encoding='utf-8') as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)

        return redirect('home')

    else:
        with open(test_path, 'r', encoding='utf-8') as f:
            datos = json.load(f)

        return render(request, 'management_test/modificar_test_inteligencias.html', {
            'filename': filename,
            'test_data': datos,
        })

@login_required
def historial_tests(request):
    titulo_query = request.GET.get('titulo', '')

    resultados = ResultadoTest.objects.filter(user=request.user)
    titulos_unicos = resultados.values_list('test_title', flat=True).distinct()

    if titulo_query:
        resultados = resultados.filter(test_title__icontains=titulo_query)


    for resultado in resultados:
        try:
            resultado.comentarioprofesor = resultado.comentariosprofessores
        except ComentariosProfessores.DoesNotExist:
            resultado.comentarioprofesor = None


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

    # Obtener el último resultado por título
    ultimos_por_titulo = (
        resultados
        .values('test_title')
        .annotate(ultimo_id=Max('id'))
    )

    # Obtener los objetos ResultadoTest correspondientes
    ultimos_resultados = ResultadoTest.objects.filter(id__in=[r['ultimo_id'] for r in ultimos_por_titulo])

    # Vincular el comentario del profesor si existe (relación uno a uno)
    for resultado in ultimos_resultados:
        try:
            resultado.comentarioprofesor = resultado.comentariosprofessores
        except ComentariosProfessores.DoesNotExist:
            resultado.comentarioprofesor = None

    context = {
        'total_tests': total_tests,
        'promedio_aciertos': promedio_aciertos or 0,
        'promedio_fallos': promedio_fallos or 0,
        'ultimos_resultados': ultimos_resultados,
    }

    return render(request, 'management_test/dashboard_usuario.html', context)

@login_required
def detalle_resultado_test(request, test_id):
    resultado = get_object_or_404(ResultadoTest, id=test_id)

    if resultado.user != request.user and not es_profesor(request.user):
        return HttpResponseForbidden("No tienes permiso para ver este resultado.")

    detalle_json = resultado.detalle
    resultados = []
    total_correctas = 0
    aciertos_por_categoria = {}

    for item in detalle_json:
        pregunta = item.get('pregunta', f"Pregunta {len(resultados)+1}")
        seleccionadas = item.get('seleccionadas', [])
        correctas = item.get('correctas', [])
        es_correcta = set(seleccionadas) == set(correctas)

        if es_correcta:
            total_correctas += 1

        categoria = item.get('categoria')
        if categoria and es_correcta:
            aciertos_por_categoria[categoria] = aciertos_por_categoria.get(categoria, 0) + 1

        resultados.append({
            'pregunta': pregunta,
            'seleccionadas': seleccionadas,
            'correctas': correctas,
            'es_correcta': es_correcta,
        })

    grafico_resultado = {
        f"Pregunta {i+1}": 1 if r['es_correcta'] else 0
        for i, r in enumerate(resultados)
    }

    tipo_test = 'inteligencias' if 'inteligencias' in resultado.test_title.lower() else 'clasico'

    context = {
        'resultado': resultado,
        'resultados': resultados,
        'aciertos': total_correctas,
        'fallos': resultado.total_preguntas - total_correctas,
        'total': resultado.total_preguntas,
        'resultados_grafico': json.dumps(grafico_resultado),
        'aciertos_por_categoria': json.dumps(aciertos_por_categoria),
        'tipo_test': tipo_test,
    }

    return render(request, 'management_test/detalle_test.html', context)

@login_required
def evaluar_test(request):
    if request.method == 'POST':
        respuestas = request.POST 
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

@login_required
@user_passes_test(es_alumno)
def formulario_usuario(request, test_id):
    resultado = get_object_or_404(ResultadoTest, id=test_id, user=request.user)
    comentario_obj = get_object_or_404(ComentariosProfessores, test=resultado)

    if request.method == "POST":
        comentario_usuario = request.POST.get("comentario_usuario")
        comentario_obj.comentario_usuario = comentario_usuario
        comentario_obj.save()
        return redirect('historial_tests')  # O donde prefieras volver

    return render(request, 'management_test/formulario_usuario.html', {
        'comentario_profesor': comentario_obj.comentario,
        'comentario_usuario': comentario_obj.comentario_usuario,
        'test': resultado,
    })

@login_required
def dashboard(request):
    user = request.user

    if user.is_staff or user.groups.filter(name='Teachers').exists():
        return redirect('dashboard_professor')  # ← este es el nombre correcto de la URL
    elif user.groups.filter(name='alumnos').exists():
        return redirect('dashboard_usuario')
    else:
        return redirect('home')  # o puedes redirigir a una vista personalizada como "sin_grupo"

def obtener_categorias_desde_json(filename):
    ruta_test = os.path.join(settings.BASE_DIR, "test", filename)
    with open(ruta_test, encoding="utf-8") as f:
        contenido = json.load(f)
    categorias = set()
    for p in contenido.get("questions", []):
        cat = p.get("categoria")
        if cat:
            categorias.add(cat)
    return sorted(categorias)

def seleccionar_preguntas_equilibradas_por_categorias(json_data, categorias_seleccionadas=None, num_preguntas_total=20):
    preguntas = json_data.get("questions", [])

    # Si no hay categorías seleccionadas, usar todas las que haya en las preguntas
    if not categorias_seleccionadas:
        categorias_seleccionadas = list({p.get("categoria") for p in preguntas if p.get("categoria")})

    # Filtrar preguntas que estén en las categorías seleccionadas
    preguntas_filtradas = [p for p in preguntas if p.get("categoria") in categorias_seleccionadas]

    # Agrupar preguntas por categoría
    preguntas_por_categoria = {}
    for p in preguntas_filtradas:
        cat = p.get("categoria")
        preguntas_por_categoria.setdefault(cat, []).append(p)

    total_categorias = len(preguntas_por_categoria)
    if total_categorias == 0:
        return []

    num_por_categoria = max(1, num_preguntas_total // total_categorias)
    faltan = num_preguntas_total - (num_por_categoria * total_categorias)

    seleccionadas = []

    # Tomar preguntas por categoría
    for cat, lista_preguntas in preguntas_por_categoria.items():
        random.shuffle(lista_preguntas)
        cantidad = num_por_categoria
        if faltan > 0:
            cantidad += 1
            faltan -= 1
        seleccionadas.extend(lista_preguntas[:cantidad])

    random.shuffle(seleccionadas)
    return seleccionadas

def seleccionar_preguntas_equilibradas(json_data, max_preguntas=20):
    preguntas_seleccionadas = []

    if not isinstance(json_data, dict) or "questions_by_category" not in json_data:
        raise ValueError("El JSON no contiene el formato esperado con 'questions_by_category'.")

    categorias = list(json_data['questions_by_category'].keys())
    n_categorias = len(categorias)
    if n_categorias == 0:
        return []

    preguntas_por_categoria = max_preguntas // n_categorias
    resto = max_preguntas % n_categorias

    for categoria in categorias:
        preguntas_cat = json_data['questions_by_category'].get(categoria, [])
        n_preguntas_cat = preguntas_por_categoria + (1 if resto > 0 else 0)
        if resto > 0:
            resto -= 1

        preguntas_cat_seleccionadas = random.sample(
            preguntas_cat,
            min(n_preguntas_cat, len(preguntas_cat))
        )
        preguntas_seleccionadas.extend([
            dict(p, **{"categoria": categoria}) for p in preguntas_cat_seleccionadas
        ])

    random.shuffle(preguntas_seleccionadas)
    return preguntas_seleccionadas

def resultado_test_inteligencias(request):
    respuestas = request.session.get("respuestas", [])
    preguntas = request.session.get("preguntas_inteligencias", [])

    if not preguntas:
        return redirect("seleccionar_categorias", filename='inteligencias_multiples.json')

    resultados = []
    aciertos_por_categoria = Counter()
    total_preguntas = len(preguntas)

    for i, pregunta in enumerate(preguntas):
        seleccionadas = respuestas[i] if i < len(respuestas) else []
        if isinstance(seleccionadas, str):
            seleccionadas = [seleccionadas]

        correctas = [opt.get('text', '') for opt in pregunta.get('options', []) if opt.get('ok')]
        es_correcta = sorted(seleccionadas) == sorted(correctas)

        categoria = pregunta.get('categoria', 'Sin categoría')
        texto_pregunta = pregunta.get('question') or pregunta.get('text') or 'Pregunta sin texto'

        if es_correcta:
            aciertos_por_categoria[categoria] += 1

        resultados.append({
            'pregunta': texto_pregunta,
            'seleccionadas': seleccionadas,
            'correctas': correctas,
            'es_correcta': es_correcta,
            'categoria': categoria,
        })

    predominante = None
    if aciertos_por_categoria:
        predominante = aciertos_por_categoria.most_common(1)[0][0]

    if request.user.is_authenticated:
        ResultadoInteligencia.objects.create(
            usuario=request.user,
            test_title='Test de Inteligencias Múltiples',
            total=total_preguntas,
            aciertos=sum(aciertos_por_categoria.values()),
            fallos=total_preguntas - sum(aciertos_por_categoria.values()),
            resultados=resultados,
            fecha=now()
        )

        resultado_test_db = ResultadoTest.objects.create(
            user=request.user,
            test_title='Test de Inteligencias Múltiples',
            filename='inteligencias_multiples.json',
            fecha=now(),
            total_preguntas=total_preguntas,
            aciertos=sum(aciertos_por_categoria.values()),
            fallos=total_preguntas - sum(aciertos_por_categoria.values()),
            detalle=resultados
        )

        for r in resultados:
            PreguntaRespondida.objects.create(
                resultado=resultado_test_db,
                pregunta=r['pregunta'],
                categoria=r['categoria'],
                respuestas_usuario=r['seleccionadas'],
                respuestas_correctas=r['correctas'],
                es_correcta=r['es_correcta']
            )

    # Limpiar sesión
    for key in ['respuestas', 'preguntas_inteligencias', 'preguntas_test']:
        request.session.pop(key, None)

    context = {
        'tipo_test': 'inteligencias',
        'resultados': resultados,
        'puntajes': dict(aciertos_por_categoria),
        'predominante': predominante,
        'aciertos': sum(aciertos_por_categoria.values()),
        'fallos': total_preguntas - sum(aciertos_por_categoria.values()),
        'total': total_preguntas,
        'grafico_datos': json.dumps(dict(aciertos_por_categoria)),
    }

    return render(request, 'management_test/resultado_test.html', context)

@login_required
@user_passes_test(es_alumno)
def realizar_test(request, filename):
    ruta_test = os.path.join(settings.BASE_DIR, "test", filename)

    # Detectar tipo de test
    es_inteligencias = "inteligencias" in filename.lower()
    key_preguntas = "preguntas_inteligencias" if es_inteligencias else "preguntas_test"

    # Cargar archivo JSON para título y descripción
    with open(ruta_test, encoding="utf-8") as f:
        contenido = json.load(f)

    titulo_test = contenido.get("title") or f"Test: {os.path.splitext(filename)[0].replace('_', ' ').title()}"
    descripcion_test = contenido.get("description", "")

    # 🧼 Reiniciar si cambió de test
    ultimo_test = request.session.get("filename")
    if ultimo_test != filename:
        request.session.pop("preguntas_test", None)
        request.session.pop("preguntas_inteligencias", None)
        request.session.pop("respuestas", None)
        request.session.pop("categorias_previas", None)
        request.session["filename"] = filename
        request.session.modified = True

    if request.method == "GET":

        # 🔁 Reiniciar test manualmente
        if request.GET.get("reiniciar") == "1":
            request.session.pop(key_preguntas, None)
            request.session.pop("respuestas", None)
            request.session.modified = True
            return redirect(f"{request.path}?pregunta=0")

        # 🎯 Test de inteligencias múltiples – regenerar si categorías cambiaron
        if es_inteligencias:
            categorias = request.session.get("categorias_seleccionadas", [])
            if not categorias:
                return redirect("seleccionar_categorias", filename=filename)

            categorias_previas = request.session.get("categorias_previas", [])
            if key_preguntas not in request.session or categorias != categorias_previas:
                preguntas = seleccionar_preguntas_equilibradas_por_categorias(
                    contenido, categorias_seleccionadas=categorias
                )
                request.session[key_preguntas] = preguntas
                request.session["respuestas"] = []
                request.session["categorias_previas"] = categorias
                request.session.modified = True
                return redirect(f"{request.path}?pregunta=0")

        # 📦 Test normal – generar si no hay preguntas cargadas
        if not es_inteligencias and key_preguntas not in request.session:
            preguntas_totales = contenido.get("questions", [])
            preguntas = random.sample(preguntas_totales, min(20, len(preguntas_totales)))
            request.session[key_preguntas] = preguntas
            request.session["respuestas"] = []
            request.session.modified = True
            return redirect(f"{request.path}?pregunta=0")

        # 👉 Cargar pregunta actual
        preguntas = request.session.get(key_preguntas, [])
        respuestas = request.session.get("respuestas", [])
        pregunta_actual = int(request.GET.get("pregunta", 0))

        if pregunta_actual >= len(preguntas):
            return redirect("resultado_test_inteligencias" if es_inteligencias else "resultado_test")

        pregunta_data = preguntas[pregunta_actual].copy()
        opciones = pregunta_data.get("options", [])
        opciones_mezcladas = random.sample(opciones, len(opciones))
        multiple_correctas = sum(1 for opcion in opciones if opcion.get("ok")) > 1

        pregunta_data["options"] = opciones_mezcladas
        pregunta_data["multiple_correctas"] = multiple_correctas

        # Obtener las respuestas guardadas para la pregunta actual
        respuestas_guardadas = []
        if len(respuestas) > pregunta_actual:
            respuestas_guardadas = respuestas[pregunta_actual]

        return render(request, "management_test/realizar_test.html", {
            "pregunta": pregunta_data,
            "numero": pregunta_actual + 1,
            "total": len(preguntas),
            "respuestas": respuestas,
            "respuestas_guardadas": respuestas_guardadas,
            "enumeracion": list(range(len(preguntas))),
            "test": {
                "title": titulo_test,
                "description": descripcion_test,
                "filename": filename,
            },
            "barra_estado": [
                {
                    "numero": idx + 1,
                    "estado": 'respondida' if idx < len(respuestas) and respuestas[idx] else 'no_respondida',
                    "actual": (idx == pregunta_actual)
                } for idx in range(len(preguntas))
            ]
        })

    # 💾 POST – guardar respuesta y avanzar
    if request.method == "POST":
        respuesta = request.POST.getlist("respuesta")
        numero = int(request.GET.get("pregunta", 0))

        respuestas = request.session.get("respuestas", [])
        while len(respuestas) <= numero:
            respuestas.append([])

        respuestas[numero] = respuesta
        request.session["respuestas"] = respuestas
        request.session.modified = True

        siguiente_pregunta = numero + 1

        if "finalizar" in request.POST or siguiente_pregunta >= len(request.session[key_preguntas]):
            return redirect("resultado_test_inteligencias" if es_inteligencias else "resultado_test")
        else:
            return redirect(f"{request.path}?pregunta={siguiente_pregunta}")

@login_required
def resultado_test(request):
    respuestas = request.session.get("respuestas", [])
    preguntas = request.session.get("preguntas_test", [])

    if not preguntas:
        return redirect("home")

    resultados = []
    aciertos = 0
    total_preguntas = len(preguntas)

    for i, pregunta in enumerate(preguntas):
        seleccionadas = respuestas[i] if i < len(respuestas) else []
        if isinstance(seleccionadas, str):
            seleccionadas = [seleccionadas]

        correctas = [opt.get('text', '') for opt in pregunta.get('options', []) if opt.get('ok')]
        es_correcta = sorted(seleccionadas) == sorted(correctas)

        texto_pregunta = pregunta.get('question') or pregunta.get('text') or 'Pregunta sin texto'
        categoria = pregunta.get('categoria', 'Sin categoría')

        if es_correcta:
            aciertos += 1

        resultados.append({
            'pregunta': texto_pregunta,
            'seleccionadas': seleccionadas,
            'correctas': correctas,
            'es_correcta': es_correcta,
            'categoria': categoria,
        })

    fallos = total_preguntas - aciertos

    if request.user.is_authenticated:
        resultado_test_db = ResultadoTest.objects.create(
            user=request.user,
            test_title='Resultado del Test',
            filename='custom',
            fecha=now(),
            total_preguntas=total_preguntas,
            aciertos=aciertos,
            fallos=fallos,
            detalle=resultados
        )

        for r in resultados:
            PreguntaRespondida.objects.create(
                resultado=resultado_test_db,
                pregunta=r['pregunta'],
                categoria=r['categoria'],
                respuestas_usuario=r['seleccionadas'],
                respuestas_correctas=r['correctas'],
                es_correcta=r['es_correcta']
            )

    # Limpiar sesión
    for key in ['respuestas', 'preguntas_test']:
        request.session.pop(key, None)

    context = {
        'tipo_test': 'normal',
        'resultados': resultados,
        'aciertos': aciertos,
        'fallos': fallos,
        'total': total_preguntas,
    }

    return render(request, 'management_test/resultado_test.html', context)


@login_required
def realizar_test_inteligencias_pregunta(request, numero):
    preguntas = request.session.get('preguntas_inteligencias')
    if not preguntas:
        return redirect('seleccionar_categorias')

    total = len(preguntas)
    numero = int(numero)

    if numero >= total:
        return redirect('resultado_test_inteligencias')

    if request.method == 'POST':
        seleccionadas = request.POST.getlist('respuesta')
        respuestas_sesion = request.session.get('respuestas', {})
        respuestas_sesion[str(numero)] = seleccionadas
        request.session['respuestas'] = respuestas_sesion
        request.session.modified = True
        return redirect('realizar_test_inteligencias_pregunta', numero=numero + 1)

    pregunta = preguntas[numero]
    respuestas_sesion = request.session.get('respuestas', {})
    barra_estado = []
    for idx in range(total):
        seleccion = respuestas_sesion.get(str(idx), [])
        estado = 'respondida' if seleccion else 'no_respondida'
        barra_estado.append({
            'numero': idx + 1,
            'estado': estado,
            'actual': (idx == numero),
        })

    context = {
        'pregunta': pregunta,
        'numero': numero + 1,
        'total': total,
        'barra_estado': barra_estado,
        'test': {
            'title': 'Test de Inteligencias Múltiples',
            'description': 'Evaluación basada en múltiples inteligencias.',
            'filename': 'inteligencias_multiples.json',
        }
    }
    return render(request, 'management_test/realizar_test.html', context)

@login_required
def seleccionar_categorias(request, filename):
    path = os.path.join(settings.BASE_DIR, 'test', filename)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return render(request, "management_test/error.html", {
            "mensaje": f"Archivo '{filename}' no encontrado."
        })

    # Extraer categorías únicas de las preguntas
    categorias = sorted(set(
        p.get('categoria') for p in data.get('questions', []) if p.get('categoria')
    ))

    if request.method == "POST":
        categorias_seleccionadas = request.POST.getlist("categorias")
        if not categorias_seleccionadas:
            return render(request, "management_test/seleccionar_categoria.html", {
                "categorias": categorias,
                "filename": filename,
                "error": "Debes seleccionar al menos una categoría.",
                "categorias_seleccionadas": [],
            })

        request.session.pop('preguntas_test', None)
        request.session.pop('respuestas', None)

        request.session['categorias_seleccionadas'] = categorias_seleccionadas

        return redirect('realizar_test', filename=filename)

    return render(request, "management_test/seleccionar_categoria.html", {
        "categorias": categorias,
        "filename": filename,
        "categorias_seleccionadas": [],
    })

@login_required
@user_passes_test(es_profesor)
def crear_test(request):
    if request.method == "POST":
        titulo = request.POST.get("titulo", "").strip()
        descripcion = request.POST.get("descripcion", "").strip()
        categoria = request.POST.get("categoria", "").strip() or None
        subcategoria = request.POST.get("subcategoria", "").strip() or None
        tags_raw = request.POST.get("tags", "").strip()
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]

        preguntas = []
        keys = list(request.POST.keys())
        indices_preguntas = set()
        for k in keys:
            if k.startswith("pregunta_"):
                try:
                    _, idx = k.split("_")
                    indices_preguntas.add(int(idx))
                except ValueError:
                    pass
        indices_preguntas = sorted(indices_preguntas)

        for i, idx in enumerate(indices_preguntas, 1):
            texto_pregunta = request.POST.get(f"pregunta_{idx}", "").strip()

            opciones = []
            opciones_claves = [k for k in keys if k.startswith(f"opcion_{idx}_")]
            indices_opciones = set()
            for k in opciones_claves:
                parts = k.split("_")
                if len(parts) == 3:
                    try:
                        _, preg_idx, opt_idx = parts
                        indices_opciones.add(int(opt_idx))
                    except ValueError:
                        pass
            indices_opciones = sorted(indices_opciones)

            for j in indices_opciones:
                texto_opcion = request.POST.get(f"opcion_{idx}_{j}", "").strip()
                if not texto_opcion:
                    continue
                ok = request.POST.get(f"ok_{idx}_{j}") == "on"
                opciones.append({"text": texto_opcion, "ok": ok})

            preguntas.append({
                "id": i,
                "question": texto_pregunta,
                "options": opciones,
                "image": None
            })

        test_json = {
            "title": titulo,
            "description": descripcion,
            "category": categoria,
            "subcategory": subcategoria,
            "tags": tags,
            "questions": preguntas,
        }

        nombre_archivo = f"{titulo.lower().replace(' ', '_')}.json"
        ruta_guardado = os.path.join(settings.BASE_DIR, "test", nombre_archivo)
        with open(ruta_guardado, "w", encoding="utf-8") as f:
            json.dump(test_json, f, indent=2, ensure_ascii=False)

        return render(request, "management_test/test_guardado_popup.html", {
            "nombre_archivo": nombre_archivo
        })

    # GET — mostrar formulario vacío
    return render(request, "management_test/crear_test.html")