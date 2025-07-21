# management_test/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  


class ResultadoTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    total_preguntas = models.PositiveIntegerField()
    aciertos = models.PositiveIntegerField()
    fallos = models.PositiveIntegerField()
    detalle = models.JSONField()
   
    def __str__(self):
        return f'{self.user.username} - {self.test_title} ({self.fecha.strftime("%Y-%m-%d")})' 
    
class ComentariosProfessores(models.Model):
    professor = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.TextField()
    test = models.OneToOneField(ResultadoTest, on_delete=models.CASCADE)
    
class PreguntaRespondida(models.Model):
    resultado = models.ForeignKey(ResultadoTest, on_delete=models.CASCADE, related_name='respuestas')
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # ← Nuevo campo
    pregunta = models.TextField()
    seleccionadas = models.JSONField()
    correctas = models.JSONField()
    es_correcta = models.BooleanField()

    def __str__(self):
        return f"{self.user.username} - {self.pregunta[:30]}... ({'✔' if self.es_correcta else '✘'})"

