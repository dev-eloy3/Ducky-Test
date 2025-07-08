from django.urls import path
from . import views

urlpatterns = [
     path('', views.enseñar_test, name='ver el test'),
     path('guardar_respuestas/', views.guardar_respuestas_view, name='guardar_respuestas'),
 ]
   
