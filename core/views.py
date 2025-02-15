from django.shortcuts import render, redirect
from accounts.utils import role_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import render
from django.utils.timezone import now
from facturacion.models import Factura, DetalleFactura
from productos.models import Iphone, Mac, Accesorio
from django.db import models
from django.db.models import Sum, Q
from datetime import datetime, timedelta
import json
from decimal import Decimal

# Vista general para redirigir según el rol
@login_required
def dashboard(request):
    if request.user.role == 'Gerente':
        return redirect('dashboard_gerente')  # Asegúrate de usar el namespace si lo configuraste
    elif request.user.role == 'Empleado':
        return redirect('dashboard_empleado')
    elif request.user.role == 'Vendedor':
        return redirect('dashboard_vendedor')
    else:
        messages.error(request, "No tienes acceso al dashboard.")
        return redirect('login')  # Si no tiene rol válido, redirigir al login

# 🔹 Función para obtener la cotización del dólar
def obtener_dolar_venta():
    return Decimal(1220)  # 🚀 Aquí puedes cambiarlo por la cotización real

# Vista específica para Gerente
@login_required
@role_required(['Gerente'])
def dashboard_gerente(request):
    total_iphones = Iphone.objects.filter(stock__gt=0).count()
    total_macs = Mac.objects.filter(stock__gt=0).count()
    total_accesorios = Accesorio.objects.filter(stock__gt=0).count()
    total_productos = total_iphones + total_macs + total_accesorios

    # 🔹 Filtrar facturas sin nota de crédito
    facturas_validas = Factura.objects.filter(notacredito__isnull=True)

    # 🔹 Calcular el total de ventas en USD
    total_ventas_usd = sum(
        factura.total / factura.dolar_venta if factura.dolar_venta else 0
        for factura in facturas_validas
    )

    # 🔹 Balance de productos vendidos
    balance_productos = []
    balance_total = 0

    # 🔍 Iterar sobre los detalles de cada factura válida
    for factura in facturas_validas:
        for detalle in factura.detalles.all():  # Obtener los productos vendidos
            producto = detalle.producto_iphone or detalle.producto_mac or detalle.producto_accesorio
            if producto:
                balance_unitario = (detalle.precio_unitario / factura.dolar_venta) - producto.costo
                balance_total += balance_unitario * detalle.cantidad
                balance_productos.append({
                    'tipo': producto.__class__.__name__,
                    'modelo': producto.modelo,
                    'precio': detalle.precio_unitario / factura.dolar_venta,  # Precio en USD
                    'costo': producto.costo,  # Costo ya guardado en USD
                    'cantidad': detalle.cantidad,
                    'balance': balance_unitario * detalle.cantidad
                })

    # 🔹 Últimas facturas registradas
    ultimas_facturas = Factura.objects.order_by('-fecha')[:5]

    contexto = {
        'total_productos': total_productos,
        'total_iphones': total_iphones,
        'total_macs': total_macs,
        'total_accesorios': total_accesorios,
        'total_facturas': facturas_validas.count(),
        'total_ventas': float(total_ventas_usd),
        'ultimas_facturas': ultimas_facturas,
        'balance_productos': balance_productos,
        'balance_total': balance_total,
    }

    return render(request, 'core/dashboard_gerente.html', contexto)

# Vista específica para Empleado
@login_required
@role_required(['Empleado'])
def dashboard_empleado(request):
    return render(request, 'core/dashboard_empleado.html', {
        'data': 'Datos relevantes para empleados',  # Pasa datos adicionales si es necesario
    })

@login_required
@role_required(['Vendedor'])
def dashboard_vendedor(request):
    # Obtener datos de inventario
    total_iphones = Iphone.objects.filter(stock__gt=0).count()
    total_macs = Mac.objects.filter(stock__gt=0).count()
    total_accesorios = Accesorio.objects.filter(stock__gt=0).count()
    total_productos = total_iphones + total_macs + total_accesorios

    # Pasar datos al template
    return render(request, 'core/dashboard_vendedor.html', {
        'data': 'Datos relevantes para vendedores',
        'total_iphones': total_iphones,
        'total_macs': total_macs,
        'total_accesorios': total_accesorios,
        'total_productos': total_productos,
    })

# Vista para que los usuarios puedan editar su perfil
@login_required
def editar_perfil(request):
    user = request.user

    if request.method == 'POST':
        # Procesar los datos enviados en el formulario
        user.first_name = request.POST.get('nombre', user.first_name)
        user.last_name = request.POST.get('apellido', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()
        messages.success(request, "Perfil actualizado exitosamente.")
        return redirect('editar_perfil')

    return render(request, 'core/editar_perfil.html', {'user': user})

@login_required
@role_required(['Vendedor'])
def inventario_vendedor(request):
    return render(request, 'core/inventario_vendedor.html')  # Asegúrate de que esta plantilla existe