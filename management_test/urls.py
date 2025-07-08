from django.urls import path
from . import views

urlpatterns = [
     path('', views.test_conocimientos_view, name='ver el test'),
 ]
   
