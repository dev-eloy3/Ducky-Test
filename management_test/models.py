# management_test/models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()  

class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Subcategoria(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='subcategorias')
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

class Tag(models.Model):
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Test(models.Model):
    subcategoria = models.ForeignKey(Subcategoria, on_delete=models.CASCADE, related_name='tests')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tags = models.ManyToManyField(Tag, related_name='tests')

    def __str__(self):
        return self.titulo

class Pregunta(models.Model):
    texto = models.CharField(max_length=255)
    nivel = models.CharField(max_length=10, choices=[
        ('básico', 'Básico'),
        ('medio', 'Medio'),
        ('avanzado', 'Avanzado')
    ])
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='preguntas')

    def __str__(self):
        return self.texto
    
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

class ResultadoInteligencia(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    resultados = models.JSONField()  # Diccionario: {inteligencia: puntuación}

    def inteligencia_predominante(self):
        return max(self.resultados, key=self.resultados.get)
