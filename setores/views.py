from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Setor
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from atividades.models import RecursoAtivo

# Create your views here.
@login_required
def cadastrar_setor(request):
    if request.user.tipo_usuario != "diretor":
        messages.error(request, "Apenas diretores podem acessar o gerenciamento de contas.")
        return redirect("dashboard")
    # Aqui buscamos todos os setores e passamos para o template, para que possam ser listados na página de cadastro
    if request.method == "POST":
        nome = request.POST.get("nome")
        if nome:
            Setor.objects.create(nome=nome)
            messages.success(request, f"Setor '{nome}' cadastrado com sucesso.")
            return redirect("cadastrar_setor")
    setores = Setor.objects.all()
    recurso_ativo, _ = RecursoAtivo.objects.get_or_create(id=1, defaults={"codigo": "01"})  # pega recurso atual
    return render(request, "setores/cadastrar_setor.html", {"setores": setores, "recurso_ativo": recurso_ativo,})

@login_required
def cadastrar_chefe(request):
    if request.method == "POST":
        setor_id = request.POST.get("setor")
        setor = get_object_or_404(Setor, id=setor_id)
        setor.chefe_imediato = request.POST.get("chefe_imediato")
        setor.cargo_chefe = request.POST.get("cargo_chefe")
        setor.portaria_chefe = request.POST.get("portaria_chefe")
        setor.matricula_chefe = request.POST.get("matricula")
        setor.save()
        messages.success(request, f"Chefe do setor '{setor.nome}' cadastrado com sucesso.")
        return redirect("cadastrar_setor")
    setores = Setor.objects.all()
    return render(request, "setores/cadastrar_setor.html", {"setores": setores,})

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

    if request.method == "POST":
        setor.nome = request.POST.get("nome")
        setor.chefe_imediato = request.POST.get("chefe_imediato")
        setor.cargo_chefe = request.POST.get("cargo_chefe")
        setor.matricula_chefe = request.POST.get("matricula")
        setor.portaria_chefe = request.POST.get("portaria_chefe")
        setor.save()
        messages.success(request, f"Setor '{setor.nome}' atualizado com sucesso.")
        return redirect("cadastrar_setor")

    return render(request, "setores/editar_setor.html", {"setor": setor})

