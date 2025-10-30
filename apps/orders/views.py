from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    context = {
        'page_title': 'Sistema de Órdenes',
        'active_tab': 'orders'
    }
    return render(request, 'orders/index.html', context)