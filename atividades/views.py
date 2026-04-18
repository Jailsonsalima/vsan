from django.shortcuts import render, redirect, get_object_or_404
from .models import Atividade
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from servidores.models import Servidor
from django.utils.dateformat import DateFormat
from datetime import datetime
from setores.models import Setor

import io, zipfile

# Create your views here.

@login_required
def cadastrar_atividade(request):
    servidores = Servidor.objects.all()
    if request.method == "POST":
        data_ida_str = request.POST.get("data_ida")
        data_retorno_str = request.POST.get("data_retorno")

        data_ida = datetime.strptime(data_ida_str, "%Y-%m-%d").date() if data_ida_str else None
        data_retorno = datetime.strptime(data_retorno_str, "%Y-%m-%d").date() if data_retorno_str else None

        atividade = Atividade.objects.create(
            dias_diarias=request.POST.get("dias_diarias"),
            pernoite=request.POST.get("pernoite"),
            transporte=request.POST.get("transporte"),
            municipio=request.POST.get("municipio"),
            objetivo=request.POST.get("objetivo"),
            data_ida=data_ida,
            data_retorno=data_retorno
        )
        ids = request.POST.getlist("servidores")
        atividade.servidores.set(Servidor.objects.filter(id__in=ids))
        atividade.save()

        return redirect("dashboard")

    return render(request, "atividades/cadastro_atividades.html", {"servidores": servidores})

def formatar_periodo(data_ida, data_retorno):
    if not data_ida or not data_retorno:
        return ""

    # Se forem no mesmo mês e ano
    if data_ida.month == data_retorno.month and data_ida.year == data_retorno.year:
        return f"{data_ida.day} a {data_retorno.day}/{data_ida.month:02d}/{data_ida.year}"
    else:
        return f"{DateFormat(data_ida).format('d/m/Y')} a {DateFormat(data_retorno).format('d/m/Y')}"

@login_required
def gerar_zip_pdfs(request, atividade_id):
    # Filtra setores cujo cargo_chefe começa com "Diretor"
    setores = Setor.objects.filter(cargo_chefe__startswith="Diretor")

    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = atividade.servidores.all()

    # cria um buffer em memória
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. PDF da atividade (sem servidores)
        html_atividade = render_to_string(
            "pdf_atividade.html",
            {
                "atividade": atividade,
                "setores": setores,  # adiciona setores filtrados
                "servidores": [],  # não lista servidores aqui
                "periodo_formatado": formatar_periodo(atividade.data_ida, atividade.data_retorno),
            }
        )
        pdf_atividade = HTML(string=html_atividade, base_url=request.build_absolute_uri('/')).write_pdf()
        zip_file.writestr(f"memorando_{atividade.id}.pdf", pdf_atividade)

        # 2. PDFs de cada servidor vinculado à atividade
        for servidor in servidores:
            setor = servidor.setor if servidor.setor else None  # pega setor vinculado

            html_servidor = render_to_string(
                "pdf_servidor.html",
                {
                    "atividade": atividade,
                    "servidores": [servidor],
                    "setor": setor,  # adiciona setor no contexto
                    "periodo_formatado": formatar_periodo(atividade.data_ida, atividade.data_retorno),
                }
            )
            pdf_servidor = HTML(string=html_servidor, base_url=request.build_absolute_uri('/')).write_pdf()

            zip_file.writestr(f"{servidor.primeiro_e_ultimo_nome()}_{servidor.id}.pdf", pdf_servidor)
            # adiciona ao ZIP em memória
            #filename = f"atividade_{atividade.id}_servidor_{servidor.id}.pdf"
            #zip_file.writestr(filename, pdf_bytes)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename="{atividade.municipio}_{atividade.id}_pdfs.zip"'
    return response
