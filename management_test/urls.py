# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='test'),
    path('test/<str:filename>/', views.realizar_test, name='realizar_test'),
    path('resultado/', views.resultado_test, name='resultado_test'),
    path('historial/', views.historial_tests, name='historial_tests'),
    path('dashboard/', views.dashboard_usuario, name='dashboard_usuario'),  # <- nuevo
    path('historial/<int:test_id>/', views.detalle_resultado_test, name='detalle_resultado_test'),
    path('formulario_professor/<int:tests_id>/', views.comentario_professor, name='comentarios'),
    path('modificar_comentario/<int:id>/', views.modificar_comentario, name='modificar'),
    path('dashboard_professor/', views.profesor_vista, name='dashboard_profe'),
]
