from django.shortcuts import render, redirect, get_object_or_404
from .models import Atividade, RecursoAtivo
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
from django.db.models import Q
from agendamentos.models import MotoristaExterno
# Create your views here.

@login_required(login_url='/login/')
def cadastrar_atividade(request):
    servidores = Servidor.objects.all()
    # carrega os motoristas externos para passar ao template, caso queira listar no formulário de cadastro
    motoristas_externos = MotoristaExterno.objects.all()
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

            # Busca ou cria recurso ativo padrão
            recurso_ativo, _ = RecursoAtivo.objects.get_or_create(id=1, defaults={"codigo": "01"})

            atividade = Atividade.objects.create(
                dias_diarias=request.POST.get("dias_diarias"),
                pernoite=request.POST.get("pernoite"),
                transporte=request.POST.get("transporte"),
                municipio=request.POST.get("municipio"),
                objetivo=request.POST.get("objetivo"),
                recurso_codigo=recurso_ativo.codigo,  # associa o código do recurso ativo
                data_ida=data_ida,
                data_retorno=data_retorno,
                n_memorando = n_memorando,
                # se quiser salvar o chefe selecionado, adicione um campo no model Atividade
                chefe_imediato=chefe,  # aqui vai a instância de Setor
                criador=request.user, # aqui salva o usuário que criou o documento
            )
            ids = request.POST.getlist("servidores")
            atividade.servidores.set(Servidor.objects.filter(id__in=ids))
            ids_motoristas = request.POST.getlist("motoristas_externos")
            atividade.motoristas_externos.set(MotoristaExterno.objects.filter(id__in=ids_motoristas))
            atividade.save()
            messages.success(request, "Atividade salva com sucesso!")
            return redirect("listar_atividades")
        except IntegrityError:
            messages.error(request, "Já existe uma atividade cadastrada com este número de memorando.")
    recurso_ativo = RecursoAtivo.objects.first()
    return render(request, "atividades/cadastro_atividades.html", {
        "servidores": servidores,
        "setores": setores,
        "recurso_ativo": recurso_ativo,
        "motoristas_externos": motoristas_externos,
    })

def formatar_periodo(data_ida, data_retorno):
    if not data_ida or not data_retorno:
        return ""

    # Se forem no mesmo mês e ano
    if data_ida.month == data_retorno.month and data_ida.year == data_retorno.year:
        return f"{data_ida.day} a {data_retorno.day}/{data_ida.month:02d}/{data_ida.year}"
    else:
        return f"{DateFormat(data_ida).format('d/m/Y')} a {DateFormat(data_retorno).format('d/m/Y')}"

@login_required(login_url='/login/')
def gerar_zip_pdfs(request, atividade_id):
    # Filtra setores cujo cargo_chefe começa com "Diretor"
    setores = Setor.objects.filter(cargo_chefe__startswith="Diretor ")

    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = atividade.servidores.all()
    motoristas_externos = atividade.motoristas_externos.all()

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

        for motorista in motoristas_externos:
            html_motorista = render_to_string(
                "pdf_servidor.html",  # reaproveitando a mesma template
                {
                    "atividade": atividade,
                    "servidores": [motorista],  # aqui usamos o objeto da iteração
                    "setor": motorista.setor if motorista.setor else None,
                    "periodo_formatado": formatar_periodo(atividade.data_ida, atividade.data_retorno),
                }
            )
            pdf_motorista = HTML(string=html_motorista, base_url=request.build_absolute_uri('/')).write_pdf()
            zip_file.writestr(f"{motorista.primeiro_e_ultimo_nome()}_{motorista.id}.pdf", pdf_motorista)

            # adiciona ao ZIP em memória
            #filename = f"atividade_{atividade.id}_servidor_{servidor.id}.pdf"
            #zip_file.writestr(filename, pdf_bytes)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename="{atividade.municipio}_{atividade.id}_pdfs.zip"'
    return response

@login_required(login_url='/login/')
def editar_atividade(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = Servidor.objects.all()
    setores = Setor.objects.all()
    motoristas_externos = MotoristaExterno.objects.all()

    if request.method == "POST":
        try:
            atividade.tipo_atividade = request.POST.get("tipo_atividade")
            atividade.dias_diarias = request.POST.get("dias_diarias")
            atividade.pernoite = request.POST.get("pernoite")
            atividade.transporte = request.POST.get("transporte")
            atividade.municipio = request.POST.get("municipio")
            atividade.objetivo = request.POST.get("objetivo")
            atividade.n_memorando = request.POST.get("n_memorando")
            recurso_ativo = RecursoAtivo.objects.first()
            atividade.recurso = recurso_ativo
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
        "motoristas_externos": motoristas_externos,
    })

from django.core.paginator import Paginator

@login_required(login_url='/login/')
def listar_atividades(request):
    usuario = request.user
    if usuario.tipo_usuario == "diretor":
        atividades = Atividade.objects.all().order_by("-data_criacao")
    else:
        atividades = Atividade.objects.filter(
            Q(criador=usuario) | Q(chefe_imediato=usuario.servidor.setor)
        ).order_by("-data_criacao")

    recurso_ativo = RecursoAtivo.objects.first()
    # Filtros
    municipio = request.GET.get("municipio") or ""
    data_inicio = request.GET.get("data_inicio") or ""
    data_fim = request.GET.get("data_fim") or ""

    if municipio:
        atividades = atividades.filter(municipio__icontains=municipio)
    if data_inicio:
        try:
            atividades = atividades.filter(data_ida__gte=data_inicio)
        except ValueError:
            pass
    if data_fim:
        try:
            atividades = atividades.filter(data_retorno__lte=data_fim)
        except ValueError:
            pass

    # Paginação
    paginator = Paginator(atividades, 10)  # 10 registros por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "atividades/listar_atividades.html", {
        "page_obj": page_obj,
        "municipio": municipio,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "recurso_ativo": recurso_ativo,  # passa para template
    })

@login_required(login_url='/login/')
def adicionar_processo_atividade(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)
    if request.method == "POST":
        numero = request.POST.get("numero_processo")
        atividade.numero_processo = numero
        atividade.save()
        messages.success(request, "Número do processo adicionado à atividade com sucesso.")
        return redirect("listar_atividades")

@login_required(login_url='/login/')
def definir_recurso(request):
    recurso_ativo, _ = RecursoAtivo.objects.get_or_create(id=1, defaults={"codigo": "01"})

    if request.method == "POST":
        codigo = request.POST.get("recurso")
        recurso_ativo.codigo = codigo
        recurso_ativo.save()
        messages.success(request, f"Recurso alterado para {codigo}")
        return redirect("definir_recurso")

    return render(request, "setores/cadastrar_setor.html", {"recurso_ativo": recurso_ativo})
