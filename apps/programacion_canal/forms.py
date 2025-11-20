# apps/programacion_canal/forms.py
from django import forms
from .models import Programa, ProgramacionSemanal, BloqueProgramacion, CategoriaPrograma

class ProgramaForm(forms.ModelForm):
    class Meta:
        model = Programa
        fields = [
            'nombre', 'codigo', 'descripcion', 'categoria',  # Cambiar tipo por categoria
            'duracion_estandar', 'color', 'estado',
            'es_serie', 'temporada', 'episodio', 'titulo_episodio'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del programa...'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
            'duracion_estandar': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
            'titulo_episodio': forms.TextInput(attrs={'placeholder': 'Título específico del episodio...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo categorías activas
        self.fields['categoria'].queryset = CategoriaPrograma.objects.filter(estado='activo')
        self.fields['categoria'].empty_label = "Seleccionar categoría..."
        
        if not self.instance.pk:
            self.fields['codigo'].required = False

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
class CategoriaProgramaForm(forms.ModelForm):
    class Meta:
        model = CategoriaPrograma
        fields = ['nombre', 'descripcion', 'color', 'estado', 'orden']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción de la categoría (opcional)...'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
            'orden': forms.NumberInput(attrs={'min': '0', 'placeholder': 'Se asignará automáticamente si se deja vacío'}),
        }
        labels = {
            'nombre': 'Nombre de la Categoría *',
            'color': 'Color (opcional)',
            'orden': 'Orden (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer campos opcionales
        self.fields['color'].required = False
        self.fields['orden'].required = False
        self.fields['descripcion'].required = False