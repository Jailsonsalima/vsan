from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Setor
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def cadastrar_setor(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        setor = Setor(nome=nome)
        setor.save()
        messages.success(request, f"Setor '{setor.nome}' cadastrado com sucesso.")
        return redirect('cadastrar_setor')
    # Aqui buscamos todos os setores e passamos para o template
    setores = Setor.objects.all()
    return render(request, 'setores/cadastrar_setor.html', {'setores': setores})


@login_required
def listar_setores(request):
    setores = Setor.objects.all()
    return render(request, 'setores/listar_setores.html', {'setores': setores})

@login_required
def excluir_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    setor.delete()
    messages.success(request, f"Setor '{setor.nome}' excluído com sucesso.")
    return redirect('cadastrar_setor')
