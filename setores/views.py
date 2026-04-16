from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Setor
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from servidores.models import Servidor

# Create your views here.
@login_required
def cadastrar_setor(request):
    # Aqui buscamos todos os setores e passamos para o template, para que possam ser listados na página de cadastro
    setores = Setor.objects.all()
    servidores = Servidor.objects.all()  # lista de servidores para o select
    if request.method == 'POST':
        nome = request.POST.get('nome')
        chefe_id = request.POST.get("chefe_imediato")
        
        # Verifica se já existe setor com esse nome
        if Setor.objects.filter(nome__iexact=nome).exists():
            messages.error(request, f"O setor '{nome}' já está cadastrado.")
        else:
            chefe = Servidor.objects.get(id=chefe_id)
            setor = Setor.objects.create(
                nome=nome,
                chefe_imediato=chefe,
                matricula_chefe=chefe.matricula
            )
            messages.success(request, f"Setor '{setor.nome}' cadastrado com sucesso.")
            return redirect('cadastrar_setor')
    
    return render(request, 'setores/cadastrar_setor.html', {'setores': setores, "servidores": servidores})


@login_required
def listar_setores(request):
    setores = Setor.objects.all()
    return render(request, 'setores/listar_setores.html', {'setores': setores})

@login_required
def excluir_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    try:
        setor.delete()
        messages.success(request, f"Setor '{setor.nome}' excluído com sucesso.")
    except ProtectedError:
        messages.error(request, f"Não foi possível excluir o setor '{setor.nome}' porque existem servidores vinculados a ele.")
    return redirect('cadastrar_setor')

@login_required
def editar_setor(request, setor_id):
    setor = get_object_or_404(Setor, id=setor_id)
    servidores = Servidor.objects.all()

    if request.method == "POST":
        setor.nome = request.POST.get("nome")
        chefe_id = request.POST.get("chefe_imediato")
        if chefe_id:
            chefe = Servidor.objects.get(id=chefe_id)
            setor.chefe_imediato = chefe
            setor.matricula_chefe = chefe.matricula
        setor.save()
        messages.success(request, f"Setor '{setor.nome}' atualizado com sucesso.")
        return redirect("cadastrar_setor")

    return render(request, "setores/editar_setor.html", {"setor": setor, "servidores": servidores})
