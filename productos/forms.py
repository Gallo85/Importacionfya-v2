from django import forms
from .models import Iphone, Mac, Accesorio, FotoProducto
from datetime import datetime, date

class BaseForm(forms.ModelForm):
    """
    Clase base que aplica el mismo diseño a todos los formularios derivados.
    """
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Extraer user sin causar error si no está presente
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control form-control-sm'})

            if isinstance(field, forms.fields.DecimalField):
                field.widget.attrs.update({'placeholder': '0.00'})

        # ✅ Convertir la fecha de "YYYY-MM-DD" a "DD/MM/AAAA" antes de mostrarse en el formulario
        if 'numero_orden' in self.fields and self.instance.pk:
            fecha = getattr(self.instance, 'numero_orden', None)
            if isinstance(fecha, date):
                self.fields['numero_orden'].initial = fecha.strftime('%d/%m/%Y')  # ✅ Forzar el formato correcto

    def clean_numero_orden(self):
        """
        Convierte la fecha ingresada en DD/MM/AAAA al formato correcto de Django.
        """
        numero_orden = self.cleaned_data.get('numero_orden')

        # ✅ Si ya es un objeto date, lo devolvemos directamente
        if isinstance(numero_orden, date):
            return numero_orden

        # ✅ Si es un string, intentamos convertirlo
        if numero_orden and isinstance(numero_orden, str):
            try:
                return datetime.strptime(numero_orden.strip(), '%d/%m/%Y').date()
            except ValueError:
                raise forms.ValidationError("Formato de fecha inválido. Usa DD/MM/AAAA.")

        return None



class IphoneForm(BaseForm):
    class Meta:
        model = Iphone
        fields = [
            'imei', 'modelo', 'color', 'estado', 'capacidad', 'version_ios', 
            'porcentaje_bateria', 'ubicacion', 'precio', 'observaciones', 
            'numero_orden', 'proveedor', 'costo'
        ]
        widgets = {
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'numero_orden': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DD/MM/AAAA'}),  # ✅ Cambiado a TextInput
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class MacForm(BaseForm):
    class Meta:
        model = Mac
        fields = [
            'imei', 'modelo', 'color', 'estado', 'capacidad', 'ram', 'pantalla', 
            'version_ios', 'ubicacion', 'precio', 'observaciones',
            'numero_orden', 'proveedor', 'costo'
        ]
        widgets = {
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'numero_orden': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DD/MM/AAAA'}),  # ✅ Formato correcto
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class AccesorioForm(BaseForm):
    class Meta:
        model = Accesorio
        fields = [
            'tipo', 'modelo', 'color', 'estado', 'ubicacion', 'precio', 'observaciones',
            'numero_orden', 'proveedor', 'costo'
        ]
        widgets = {
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'numero_orden': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DD/MM/AAAA'}),  # ✅ Ahora muestra DD/MM/AAAA
            'costo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    def save(self, commit=True):
        # Inicializar stock en 1 al guardar un nuevo accesorio
        instance = super().save(commit=False)
        if not instance.pk:  # Si es un nuevo objeto
            instance.stock = 1
        if commit:
            instance.save()
        return instance


class FotoProductoForm(BaseForm):
    class Meta:
        model = FotoProducto
        fields = ['foto']

