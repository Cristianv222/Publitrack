# apps/programacion_canal/forms.py
from django import forms
from .models import Programa, ProgramacionSemanal, BloqueProgramacion

class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = [
            'nombre', 'codigo', 'descripcion', 'tipo', 
            'duracion_estandar', 'color', 'estado',
            'es_serie', 'temporada', 'episodio', 'titulo_episodio'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del programa...'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
            'duracion_estandar': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
            'titulo_episodio': forms.TextInput(attrs={'placeholder': 'Título específico del episodio...'}),
        }
        labels = {
            'duracion_estandar': 'Duración Estándar',
            'es_serie': 'Es una serie',
            'titulo_episodio': 'Título del Episodio',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el código opcional si es un nuevo programa (se generará automáticamente)
        if not self.instance.pk:  # Si es un nuevo programa
            self.fields['codigo'].required = False
            self.fields['codigo'].help_text = 'Opcional. Si se deja vacío, se generará automáticamente.'

class ProgramacionSemanalForm(forms.ModelForm):
    class Meta:
        model = ProgramacionSemanal
        fields = ['nombre', 'codigo', 'fecha_inicio_semana', 'fecha_fin_semana', 'estado']
        widgets = {
            'fecha_inicio_semana': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin_semana': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'fecha_inicio_semana': 'Fecha Inicio (Lunes)',
            'fecha_fin_semana': 'Fecha Fin (Domingo)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer el código opcional si es una nueva programación
        if not self.instance.pk:
            self.fields['codigo'].required = False
            self.fields['codigo'].help_text = 'Opcional. Si se deja vacío, se generará automáticamente.'

class BloqueProgramacionForm(forms.ModelForm):
    class Meta:
        model = BloqueProgramacion
        fields = ['programa', 'programacion_semanal', 'dia_semana', 'hora_inicio', 'duracion_real', 'es_repeticion', 'notas']
        widgets = {
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'duracion_real': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
            'notas': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Notas adicionales...'}),
        }
        labels = {
            'duracion_real': 'Duración Real',
            'es_repeticion': 'Es Repetición',
        }