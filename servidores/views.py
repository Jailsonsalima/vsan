from django.shortcuts import render, redirect
from .models import Servidor
from setores.models import Setor
from django.contrib.auth.decorators import login_required

@login_required
def cadastro_servidor(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        servidor = Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.user.matricula,  # usa matrícula do usuário
            lotacao=request.POST.get("lotacao"),
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            chefia=request.POST.get("chefia"),
        )
        # Vincula o servidor ao usuário logado
        request.user.servidor = servidor
        request.user.save()
        return redirect("dashboard")  # rota para segunda etapa de cadastro
    
    # Se for GET, mostra o formulário
    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})

def lista_servidores(request):
    servidores = Servidor.objects.all()
    return render(request, "servidores/lista_servidores.html", {"servidores": servidores})


def cadastro_servidor_publico(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.POST.get("matricula"),  # matrícula obrigatória
            lotacao=request.POST.get("lotacao"),
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            chefia=request.POST.get("chefia"),
        )
        return redirect("sucesso")

    return render(request, "servidores/cadastro_servidor_publico.html", {"setores": setores})
