from django.db import models

class TestResult(models.Model):
    # User_id = models.ForeignKey(User, on_delete=models.CASCADE)
    # Test_id = models.ForeignKey(Test, on_delete=models.CASCADE)
    Fecha = models.DateTimeField(auto_now_add=True)
    pregunta = models.IntegerField()
    respuesta = models.IntegerField()
    respuesta_corecta = models.BooleanField(default=True) 









   
