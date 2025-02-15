from django.shortcuts import render, redirect, get_object_or_404
from .models import Iphone, Mac, Accesorio, FotoProducto
from .forms import IphoneForm, MacForm, AccesorioForm, FotoProductoForm
from django.contrib.contenttypes.models import ContentType
from accounts.utils import role_required
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.contrib import messages
import requests
from django.conf import settings
from django.core.paginator import Paginator

@login_required
@role_required(['Gerente', 'Empleado', 'Vendedor'])  
def inventario(request):
    modelo = request.GET.get('modelo', '')
    tipo = request.GET.get('tipo', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    imei = request.GET.get('imei', '')

    productos = []

    # Diccionario con los modelos
    modelos = {'iphone': Iphone, 'mac': Mac, 'accesorio': Accesorio}

    # Obtener productos filtrados por tipo
    if tipo.lower() in modelos:
        queryset = modelos[tipo.lower()].objects.filter(stock__gt=0)
    else:
        queryset = list(Iphone.objects.filter(stock__gt=0)) + \
                   list(Mac.objects.filter(stock__gt=0)) + \
                   list(Accesorio.objects.filter(stock__gt=0))

    # Filtrar productos
    if modelo:
        queryset = [p for p in queryset if modelo.lower() in p.modelo.lower()]
    if precio_min:
        queryset = [p for p in queryset if p.precio and p.precio >= float(precio_min)]
    if precio_max:
        queryset = [p for p in queryset if p.precio and p.precio <= float(precio_max)]
    if imei:
        queryset = [p for p in queryset if hasattr(p, 'imei') and imei in p.imei]

    # Construir la lista de productos con su tipo
    for p in queryset:
        if isinstance(p, Iphone):
            productos.append({'tipo': 'iphone', 'obj': p, 'pk': p.pk})
        elif isinstance(p, Mac):
            productos.append({'tipo': 'mac', 'obj': p, 'pk': p.pk})
        elif isinstance(p, Accesorio):
            productos.append({'tipo': 'accesorio', 'obj': p, 'pk': p.pk})

    # Implementación de paginación
    paginator = Paginator(productos, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'productos/inventario.html', {
        'productos': page_obj,
        'filtros': {'modelo': modelo, 'tipo': tipo, 'precio_min': precio_min, 'precio_max': precio_max, 'imei': imei},
    })


def obtener_dolar_venta():
    """
    Obtiene el valor del dólar venta desde la API configurada.
    """
    try:
        response = requests.get(settings.DOLAR_API_ENDPOINT, timeout=5)
        response.raise_for_status()
        datos = response.json()
        if isinstance(datos, list):
            for item in datos:
                if item.get("casa") == "blue":
                    return float(item.get("venta", 0))
        return float(datos.get("blue", {}).get("venta", 0))
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud a la API: {e}")
        return 0


@login_required
@role_required(['Gerente'])  # Solo Gerentes pueden crear productos
def crear_producto(request, tipo):
    dolar_venta = obtener_dolar_venta()

    if dolar_venta <= 0:
        messages.error(request, "No se pudo obtener la cotización del dólar. Intenta nuevamente más tarde.")
        return redirect('crear_producto', tipo=tipo)

    modelos = {
        'iphone': (Iphone, IphoneForm),
        'mac': (Mac, MacForm),
        'accesorio': (Accesorio, AccesorioForm),
    }

    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    modelo, Formulario = modelos[tipo]
    form = Formulario(request.POST or None, request.FILES or None, user=request.user)  # ✅ Se pasa el usuario

    if request.method == 'POST' and form.is_valid():
        try:
            producto = form.save(commit=False)

            # ✅ Obtener y validar precio en dólares
            precio_dolares = request.POST.get('precio_dolares', '').strip()
            if not precio_dolares:
                messages.error(request, "Debes ingresar un precio en dólares.")
                return render(request, 'productos/crear_producto.html', {'form': form, 'dolar_venta': dolar_venta, 'tipo': tipo})

            try:
                producto.precio = Decimal(precio_dolares)  # Guardar precio en USD
                producto.precio_pesos = producto.precio * Decimal(dolar_venta)  # Convertir a ARS
            except Exception as e:
                messages.error(request, f"Error en el cálculo del precio: {e}")
                return render(request, 'productos/crear_producto.html', {'form': form, 'dolar_venta': dolar_venta, 'tipo': tipo})

            # ✅ Solo los Gerentes pueden asignar información confidencial
            if request.user.groups.filter(name='Gerente').exists():
                numero_orden = request.POST.get('numero_orden', '').strip()
                proveedor = request.POST.get('proveedor', '').strip()
                costo = request.POST.get('costo', '').strip()

                if numero_orden:
                    producto.numero_orden = numero_orden
                if proveedor:
                    producto.proveedor = proveedor
                if costo:
                    try:
                        producto.costo = Decimal(costo)
                    except:
                        messages.error(request, "El costo ingresado no es válido.")
                        return render(request, 'productos/crear_producto.html', {'form': form, 'dolar_venta': dolar_venta, 'tipo': tipo})

            producto.save()

            # 🔹 Guardar fotos si se suben
            fotos = request.FILES.getlist('fotos')
            if fotos:
                for i, foto in enumerate(fotos):
                    FotoProducto.objects.create(
                        content_type=ContentType.objects.get_for_model(producto),
                        object_id=producto.pk,
                        foto=foto,
                        es_principal=(i == 0)
                    )

            messages.success(request, f"Producto creado correctamente con precio en pesos: ${producto.precio_pesos:.2f} ARS.")
            return redirect('inventario')

        except Exception as e:
            messages.error(request, f"Error al guardar el producto: {e}")

    return render(request, 'productos/crear_producto.html', {
        'form': form,
        'dolar_venta': dolar_venta,
        'tipo': tipo,
    })



@login_required
@role_required(['Gerente'])  # ✅ Solo los Gerentes pueden editar productos
def editar_producto(request, tipo, pk):
    dolar_venta = obtener_dolar_venta()

    modelos = {'iphone': (Iphone, IphoneForm), 'mac': (Mac, MacForm), 'accesorio': (Accesorio, AccesorioForm)}

    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    modelo, Formulario = modelos[tipo]
    producto = get_object_or_404(modelo, pk=pk)

    form = Formulario(request.POST or None, request.FILES or None, instance=producto, user=request.user)  # ✅ Se pasa el usuario

    if request.method == 'POST' and form.is_valid():
        producto = form.save(commit=False)

        # ✅ Solo los Gerentes pueden modificar los datos sensibles
        if request.user.groups.filter(name='Gerente').exists():
            if 'numero_orden' in form.changed_data:
                producto.numero_orden = form.cleaned_data['numero_orden']
            if 'proveedor' in form.changed_data:
                producto.proveedor = form.cleaned_data['proveedor']
            if 'costo' in form.changed_data:
                producto.costo = Decimal(form.cleaned_data['costo']) if form.cleaned_data['costo'] else 0

        # ✅ Recalcular precio en pesos si cambia el precio en dólares
        if 'precio' in form.changed_data:
            producto.precio_pesos = Decimal(producto.precio) * Decimal(dolar_venta)

        producto.save()

        messages.success(request, "Producto actualizado correctamente.")
        return redirect('inventario')

    return render(request, 'productos/editar_producto.html', {
        'form': form,
        'tipo': tipo,
        'producto': producto,
        'dolar_venta': dolar_venta,
    })



@login_required
@role_required(['Gerente'])  # Solo Gerente puede acceder
def eliminar_producto(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    producto.delete()
    return redirect('inventario')


@login_required
def seleccionar_tipo_producto(request):
    return render(request, 'productos/seleccionar_tipo_producto.html')


@login_required
def ver_producto(request, tipo, pk):
    modelos = {'iphone': Iphone, 'mac': Mac, 'accesorio': Accesorio}

    if tipo not in modelos:
        messages.error(request, "Tipo de producto inválido.")
        return redirect('inventario')

    producto = get_object_or_404(modelos[tipo], pk=pk)

    content_type = ContentType.objects.get_for_model(producto)
    fotos = FotoProducto.objects.filter(content_type=content_type, object_id=producto.pk)

    # ✅ Determinar si el usuario tiene el rol de Gerente
    es_gerente = request.user.role == 'Gerente'  # 🔹 Cambio aquí

    return render(request, 'productos/ver_producto.html', {
        'producto': producto,
        'tipo': tipo,
        'fotos': fotos,
        'es_gerente': es_gerente,  # ✅ Se pasa esta variable a la plantilla
    })


@login_required
def imprimir_qr(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    return render(request, 'productos/imprimir_qr.html', {'producto': producto})

@login_required
def imprimir_descripcion(request, tipo, pk):
    if tipo == 'iphone':
        producto = get_object_or_404(Iphone, pk=pk)
    elif tipo == 'mac':
        producto = get_object_or_404(Mac, pk=pk)
    elif tipo == 'accesorio':
        producto = get_object_or_404(Accesorio, pk=pk)
    else:
        return redirect('inventario')

    # Obtener fotos adicionales del producto (si existen)
    content_type = ContentType.objects.get_for_model(producto)
    fotos = FotoProducto.objects.filter(content_type=content_type, object_id=producto.pk)

    return render(request, 'productos/imprimir_descripcion.html', {
        'producto': producto,
        'tipo': tipo,
        'fotos': fotos,
    })