from django.shortcuts import render, redirect
from .models import Atividade

# Create your views here.
from django.contrib.auth.decorators import login_required

@login_required
def cadastrar_atividade(request):
    if request.method == "POST":
        servidor = request.user.servidor if hasattr(request.user, "servidor") else None

        atividade = Atividade.objects.create(
            servidor_nome=servidor.nome if servidor else "Sem servidor",
            servidor_matricula=servidor.matricula if servidor else None,
            servidor_cargo=servidor.cargo if servidor else None,

            tipo_atividade=request.POST.get("tipo_atividade"),
            #periodo_viagem=request.POST.get("periodo_viagem"),
            dias_diarias=request.POST.get("dias_diarias"),
            pernoite=request.POST.get("pernoite"),
            transporte=request.POST.get("transporte"),
            objetivo=request.POST.get("objetivo"),
            data_ida=request.POST.get("data_ida") or None,
            data_retorno=request.POST.get("data_retorno") or None
        )
        return redirect("lista_servidores")  # rota para selecionar os servidores cadastrados para gerar o PDF
        #return render(request, "servidores/lista_servidores.html", {"atividade": atividade})

    return render(request, "atividades/cadastro_atividades.html")
