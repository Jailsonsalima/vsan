from django.shortcuts import render, redirect, get_object_or_404
from .models import Atividade
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from servidores.models import Servidor

# Create your views here.

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
        return redirect("selecionar_servidores", atividade_id=atividade.id)  # rota para selecionar os servidores cadastrados para gerar o PDF
        #return render(request, "servidores/lista_servidores.html", {"atividade": atividade})

    return render(request, "atividades/cadastro_atividades.html")


@login_required
def selecionar_servidores(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)

    if request.method == "POST":
        ids = request.POST.getlist("servidores")
        servidores = Servidor.objects.filter(id__in=ids)
        atividade.servidores.set(servidores)
        atividade.save()

        # gerar PDF com dados da atividade + servidores
        html_string = render_to_string(
            "pdf_modelo.html",
            {"atividade": atividade, "servidores": servidores}
        )
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response['Content-Disposition'] = 'inline; filename="atividade.pdf"'
        return response

    servidores = Servidor.objects.all()
    return render(request, "servidores/selecionar_servidores.html", {"servidores": servidores, "atividade": atividade})
