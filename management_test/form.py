from django import forms
from .models import ComentariosProfessores

class ComentarioForm(forms.ModelForm):
    class Meta:
        model = ComentariosProfessores
        fields = ['comentario']

