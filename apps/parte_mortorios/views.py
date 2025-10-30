from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    context = {
        'page_title': 'Parte Mortorios',
        'active_tab': 'parte_mortorios'
    }
    return render(request, 'parte_mortorios/index.html', context)