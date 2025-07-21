from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# Resultados clásicos
class ResultadoTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test_title = models.CharField(max_length=255)
    filename = models.CharField(max_length=255, null=True, blank=True)
    aciertos = models.IntegerField()
    fallos = models.IntegerField()
    total_preguntas = models.IntegerField()
    detalle = models.JSONField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test_title} ({self.fecha.strftime('%Y-%m-%d')})"

class PreguntaRespondida(models.Model):
    resultado = models.ForeignKey(ResultadoTest, on_delete=models.CASCADE)
    pregunta = models.TextField()
    categoria = models.CharField(max_length=100)
    respuestas_correctas = models.JSONField()
    respuestas_usuario = models.JSONField()
    es_correcta = models.BooleanField()

# Resultados de inteligencias múltiples
class ResultadoInteligencia(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    test_title = models.CharField(max_length=255)
    aciertos = models.IntegerField()
    fallos = models.IntegerField()
    total = models.IntegerField()
    resultados = models.JSONField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.test_title} - Total: {self.total}"


# Comentarios de profesores
class ComentariosProfessores(models.Model):
    professor = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.OneToOneField(ResultadoTest, on_delete=models.CASCADE)
    comentario = models.TextField()
    comentario_usuario = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Comentario de {self.professor.username} sobre {self.test.test_title}"
