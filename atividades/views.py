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
from django.contrib import messages
import io, zipfile
from django.db import IntegrityError

# Create your views here.

@login_required
def cadastrar_atividade(request):
    servidores = Servidor.objects.all()
    # Filtra setores cujo cargo_chefe NÃO começa com "Diretor"
    setores = Setor.objects.exclude(cargo_chefe__startswith="Diretor")
    if request.method == "POST":
        try:
            setor_id = request.POST.get("setor")
            setor = Setor.objects.get(id=setor_id) if setor_id else None
            chefe_id = request.POST.get("chefe_imediato")  # pega o chefe selecionado
            chefe = Setor.objects.get(id=chefe_id) if chefe_id else None

            data_ida_str = request.POST.get("data_ida")
            data_retorno_str = request.POST.get("data_retorno")

            data_ida = datetime.strptime(data_ida_str, "%Y-%m-%d").date() if data_ida_str else None
            data_retorno = datetime.strptime(data_retorno_str, "%Y-%m-%d").date() if data_retorno_str else None
            n_memorando = request.POST.get("n_memorando")
            chefe_id = request.POST.get("chefe_imediato")
            chefe = Setor.objects.get(id=chefe_id) if chefe_id else None
            atividade = Atividade.objects.create(
                dias_diarias=request.POST.get("dias_diarias"),
                pernoite=request.POST.get("pernoite"),
                transporte=request.POST.get("transporte"),
                municipio=request.POST.get("municipio"),
                objetivo=request.POST.get("objetivo"),
                recurso=request.POST.get("recurso"),
                data_ida=data_ida,
                data_retorno=data_retorno,
                n_memorando = n_memorando,
                # se quiser salvar o chefe selecionado, adicione um campo no model Atividade
                chefe_imediato=chefe,  # aqui vai a instância de Setor
            )
            ids = request.POST.getlist("servidores")
            atividade.servidores.set(Servidor.objects.filter(id__in=ids))
            atividade.save()
            messages.success(request, "Atividade salva com sucesso!")
            return redirect("dashboard")
        except IntegrityError:
            messages.error(request, "Já existe uma atividade cadastrada com este número de memorando.")

    return render(request, "atividades/cadastro_atividades.html", {
        "servidores": servidores,
        "setores": setores
    })

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

@login_required
def editar_atividade(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = Servidor.objects.all()
    setores = Setor.objects.all()

    if request.method == "POST":
        try:
            atividade.tipo_atividade = request.POST.get("tipo_atividade")
            atividade.dias_diarias = request.POST.get("dias_diarias")
            atividade.pernoite = request.POST.get("pernoite")
            atividade.transporte = request.POST.get("transporte")
            atividade.municipio = request.POST.get("municipio")
            atividade.objetivo = request.POST.get("objetivo")
            atividade.n_memorando = request.POST.get("n_memorando")
            atividade.recurso = request.POST.get("recurso")
            data_ida_str = request.POST.get("data_ida")
            data_retorno_str = request.POST.get("data_retorno")
            atividade.data_ida = datetime.strptime(data_ida_str, "%Y-%m-%d").date() if data_ida_str else None
            atividade.data_retorno = datetime.strptime(data_retorno_str, "%Y-%m-%d").date() if data_retorno_str else None

            chefe_id = request.POST.get("chefe_imediato")
            atividade.chefe_imediato = Setor.objects.get(id=chefe_id) if chefe_id else None

            ids = request.POST.getlist("servidores")
            atividade.servidores.set(Servidor.objects.filter(id__in=ids))

            atividade.save()
            messages.success(request, "Atividade atualizada com sucesso!")
            return redirect("dashboard")
        except IntegrityError:
            messages.error(request, "Já existe uma atividade cadastrada com este número de memorando.")
            return redirect("editar_atividade", atividade_id=atividade.id)

    return render(request, "atividades/editar_atividade.html", {
        "atividade": atividade,
        "servidores": servidores,
        "setores": setores,
    })

from django.core.paginator import Paginator

@login_required
def listar_atividades(request):
    atividades = Atividade.objects.all().order_by("-data_criacao")

    # Filtros
    municipio = request.GET.get("municipio")
    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    if municipio:
        atividades = atividades.filter(municipio__icontains=municipio)
    if data_inicio:
        atividades = atividades.filter(data_ida__gte=data_inicio)
    if data_fim:
        atividades = atividades.filter(data_retorno__lte=data_fim)

    # Paginação
    paginator = Paginator(atividades, 10)  # 10 registros por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "atividades/listar_atividades.html", {
        "page_obj": page_obj,
        "municipio": municipio,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })
