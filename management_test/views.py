from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.conf import settings
from .models import TestResult
from django.utils import timezone
import json
import os

def enseñar_test(request):
   # Ruta al archivo JSON
  ruta_json = os.path.join(settings.BASE_DIR, 'test', 'python_avanzado_test.json') 

     # Leer el archivo
  with open(ruta_json, 'r', encoding='utf-8') as archivo:
        test_data = json.load(archivo)

  # Enviar el contenido al template
  return render(request, 'test_conocimientos.html', {'test': test_data})

def guardar_respuestas_view(request):
    
    if request.method == 'POST':
        ruta_json = os.path.join(settings.BASE_DIR, 'test', 'python_avanzado_test.json')
        with open(ruta_json, 'r', encoding='utf-8') as archivo:
            test_data = json.load(archivo)

        for pregunta in test_data["questions"]:
            pregunta_id = pregunta["id"]
            respuesta_id = request.POST.get(f'pregunta_{pregunta_id}')

            if respuesta_id:
                # Buscar la opción seleccionada dentro de la pregunta
                opcion_elegida = None
                for opcion in pregunta["options"]:
                    # Comprobamos si la opción tiene un ID y coincide con la respuesta
                    if str(opcion.get("id")) == str(respuesta_id):
                        opcion_elegida = opcion
                        break
            
            if opcion_elegida:
                TestResult.objects.create(
                    Fecha=timezone.now(),
                    pregunta=pregunta["id"],
                    Respuesta = int(respuesta_id),
                    Respuesta_corecta=opcion_elegida.get("ok", False)
                )

        return redirect('ver el test') 
    return HttpResponse("Método no permitido", status=405)


