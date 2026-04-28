from django.shortcuts import render, redirect
from .models import Servidor
from setores.models import Setor
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.contrib import messages

@login_required(login_url='/login/')
def cadastro_servidor(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        setor_id = request.POST.get("setor")
        setor = Setor.objects.get(id=setor_id) if setor_id else None
        nascimento_str = request.POST.get("nascimento")
        nascimento = None
        if nascimento_str:
            try:
                nascimento = datetime.strptime(nascimento_str, "%Y-%m-%d").date()
                # Calcula idade
                hoje = date.today()
                idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
                if idade < 18:
                    messages.error(request, "O servidor deve ter pelo menos 18 anos.")
                    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            
        servidor = Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.user.matricula,  # usa matrícula do usuário
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            setor=setor,  # vínculo com setor
           
        )
        # Vincula o servidor ao usuário logado
        request.user.servidor = servidor
        request.user.save()
        messages.success(request, "Servidor cadastrado com sucesso! ")
        return redirect("dashboard")  # rota para segunda etapa de cadastro
    
    # Se for GET, mostra o formulário
    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})

def lista_servidores(request):
    servidores = Servidor.objects.all()
    return render(request, "servidores/lista_servidores.html", {"servidores": servidores})


def cadastro_servidor_publico(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        setor_id = request.POST.get("setor")
        setor = Setor.objects.get(id=setor_id) if setor_id else None
        nascimento_str = request.POST.get("nascimento")
        nascimento = None
        if nascimento_str:
            try:
                nascimento = datetime.strptime(nascimento_str, "%Y-%m-%d").date()
                # Calcula idade
                hoje = date.today()
                idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
                if idade < 18:
                    messages.error(request, "O servidor deve ter pelo menos 18 anos.")
                    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            
        Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.POST.get("matricula"),  # matrícula obrigatória
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            setor=setor,  # vínculo com setor
        )
        messages.success(request, "Servidor público cadastrado com sucesso! ")
        return redirect("sucesso")
    

    return render(request, "servidores/cadastro_servidor_publico.html", {"setores": setores})
