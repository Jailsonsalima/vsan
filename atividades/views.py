from django.shortcuts import render, redirect, get_object_or_404
from .models import Atividade, RecursoAtivo, DiaEspecial, ValorDiaria
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from servidores.models import Servidor, HistoricoSituacao
from django.utils.dateformat import DateFormat
from datetime import datetime, date
from setores.models import Setor
from django.contrib import messages
import io, zipfile
from django.db import IntegrityError
from django.db.models import Q
from agendamentos.models import MotoristaExterno, Agendamento
# Create your views here.
import calendar
import locale
from django.utils import timezone
from django.core.paginator import Paginator

from veiculos.models import Veiculo

locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

import unicodedata

def normalizar(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    ).lower().strip()

@login_required(login_url='/login/')
def cadastrar_atividade(request, agendamento_id=None):
    servidores = Servidor.objects.all()
    # carrega os motoristas externos para passar ao template, caso queira listar no formulário de cadastro
    motoristas_externos = MotoristaExterno.objects.all()
    # Filtra setores cujo cargo_chefe NÃO começa com "Diretor"
    setores = Setor.objects.exclude(cargo_chefe__startswith="Diretor")
    agendamento = None
    motorista_sorteado = None
    if agendamento_id:
        agendamento = get_object_or_404(Agendamento, id=agendamento_id)
        # pega o processamento já criado
        processamento = getattr(agendamento, "processamento", None)
        if processamento and processamento.motorista_servidor:
            motorista_sorteado = processamento.motorista_servidor
        elif processamento and processamento.motorista_externo:
            motorista_sorteado = processamento.motorista_externo
    if request.method == "POST":
        try:
            setor_id = request.POST.get("setor")
            setor = Setor.objects.get(id=setor_id) if setor_id else None
            chefe_id = request.POST.get("chefe_imediato")  # pega o chefe selecionado
            chefe = Setor.objects.get(id=chefe_id) if chefe_id else None

            data_ida_str = request.POST.get("data_ida")
            data_retorno_str = request.POST.get ("data_retorno")

            data_ida = datetime.strptime(data_ida_str, "%Y-%m-%d").date() if data_ida_str else None
            data_retorno = datetime.strptime(data_retorno_str, "%Y-%m-%d").date() if data_retorno_str else None
            n_memorando = request.POST.get("n_memorando")
            if not n_memorando or not n_memorando.strip():
                n_memorando = None
            # Busca ou cria recurso ativo padrão
            recurso_ativo, _ = RecursoAtivo.objects.get_or_create(id=1, defaults={"codigo": "01"})

            ids = request.POST.getlist("servidores")

            servidores_selecionados = Servidor.objects.filter(id__in=ids)
            # Verificação de conflito em lote
            conflitos = Atividade.objects.filter(
                servidores__in=servidores_selecionados,
                data_ida__lte=data_retorno,
                data_retorno__gte=data_ida
            ).exclude(agendamento=agendamento).exclude(agendamento__status="cancelado")  # 👈 exclui da verificação o próprio agendamento e os que estiverem em agendamentos cancelados

            if conflitos.exists():
                # pega todos os servidores envolvidos nos conflitos
                servidores_conflito = set()
                for atividade in conflitos:
                    for servidor in atividade.servidores.all():
                        if servidor in servidores_selecionados:
                            servidores_conflito.add(servidor.nome)

                nomes_conflito = ", ".join(servidores_conflito)
                messages.error(request, f"Os seguintes servidores já possuem agendamento neste mesmo período:\n {nomes_conflito}")
                return redirect("cadastrar_atividade_agendamento", agendamento_id=agendamento.id)

            # Se não houver conflito, cria a atividade normalmente
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
                agendamento=agendamento,
                # se quiser salvar o chefe selecionado, adicione um campo no model Atividade
                chefe_imediato=chefe,  # aqui vai a instância de Setor
                criador=request.user, # aqui salva o usuário que criou o documento
            )
            # vincula servidores e motoristas
            atividade.servidores.set(Servidor.objects.filter(id__in=ids))
            ids_motoristas = request.POST.getlist("motoristas_externos")
            atividade.motoristas_externos.set(MotoristaExterno.objects.filter(id__in=ids_motoristas))
            atividade.save()
            messages.success(request, "Atividade salva com sucesso!")
            return redirect("listar_atividades")
        except IntegrityError:
            messages.error(request, "Já existe uma atividade cadastrada com este número de memorando.")
    # Monta lista de servidores com status de conflito
    servidores_conflito_ids = set()
    if agendamento and agendamento.data_ida and agendamento.data_retorno:
        conflitos = Atividade.objects.filter(
            servidores__in=servidores,
            data_ida__lte=agendamento.data_retorno,
            data_retorno__gte=agendamento.data_ida
        ).exclude(agendamento=agendamento).exclude(agendamento__status="cancelado")
        for atividade in conflitos:
            for servidor in atividade.servidores.all():
                servidores_conflito_ids.add(servidor.id)

    servidores_status = []
    for servidor in servidores:
        em_conflito = servidor.id in servidores_conflito_ids
        servidores_status.append({"servidor": servidor, "em_conflito": em_conflito})
    
    ocultar_diarias = False
    if agendamento and agendamento.municipio:
        municipios_sem_diarias = [
            "Belém", "Ananindeua", "Benevides", "Marituba",
            "Santa Bárbara do Pará", "Santa Isabel do Pará",
            "Castanhal", "Barcarena"
        ]
        # normaliza toda a lista
        municipios_sem_diarias = [normalizar(m) for m in municipios_sem_diarias]

        # normaliza o valor selecionado
        municipio_normalizado = normalizar(agendamento.municipio)

        if municipio_normalizado in municipios_sem_diarias:
            ocultar_diarias = True
        # se o município tiver qualquer parte igual a um dos nomes da lista, ele já oculta
        #if any(m in municipio_normalizado for m in municipios_sem_diarias):

    return render(request, "atividades/cadastro_atividades.html", {
        "servidores_status": servidores_status,
        "setores": setores,
        "recurso_ativo": RecursoAtivo.objects.first(),
        "motoristas_externos": motoristas_externos,
        "motorista_sorteado": motorista_sorteado,
        "agendamento": agendamento,
        "ocultar_diarias": ocultar_diarias,
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
    # Filtra setores cujo nome começa com "DEVS"
    setores = Setor.objects.filter(nome__startswith="DEVS")

    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = atividade.servidores.all().order_by("nome")
    motoristas_externos = atividade.motoristas_externos.all()

    # Filtra setores: só mantém aqueles cujo chefe não está listado como servidor
    setor_dvs = Setor.objects.filter(nome__startswith="DVS")

    # Verifica se o chefe imediato está entre os servidores
    chefe_matricula = atividade.chefe_imediato.matricula_chefe if atividade.chefe_imediato else None
    chefe_eh_servidor = False
    if chefe_matricula:
        chefe_eh_servidor = servidores.filter(matricula=chefe_matricula).exists()

    setores_filtrados = []

    for setor in setores:
        # Se o diretor foi selecionado como servidor, não adiciona ele
        if not servidores.filter(matricula=setor.matricula_chefe).exists():
            setores_filtrados.append(setor)
        else:
            # Se o diretor foi selecionado, adiciona a diretora
            setores_filtrados.extend(setor_dvs)

    # cria um buffer em memória
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. PDF da atividade (sem servidores)
        html_atividade = render_to_string(
            "pdf_atividade.html",
            {
                "atividade": atividade,
                "setores": setores_filtrados,  # adiciona setores filtrados
                "servidores": [],  # não lista servidores aqui
                "periodo_formatado": formatar_periodo(atividade.data_ida, atividade.data_retorno),
                "chefe_eh_servidor": chefe_eh_servidor,
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
    transporte_choices = Agendamento._meta.get_field("transporte").choices

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
            atividade.data_criacao = timezone.now()
            atividade.save()

            # Atualiza também o agendamento vinculado
            if atividade.agendamento:
                atividade.agendamento.municipio = atividade.municipio
                atividade.agendamento.transporte = atividade.transporte
                atividade.agendamento.data_ida = atividade.data_ida
                atividade.agendamento.data_retorno = atividade.data_retorno
                atividade.agendamento.motivo = atividade.objetivo
                atividade.agendamento.save()
            messages.success(request, "Atividade atualizada com sucesso!")
            return redirect("listar_atividades")
        except IntegrityError:
            messages.error(request, "Já existe uma atividade cadastrada com este número de memorando.")
            return redirect("editar_atividade", atividade_id=atividade.id)
    # Verificação de conflitos
    servidores_conflito_ids = set()
    if atividade.data_ida and atividade.data_retorno:
        conflitos = Atividade.objects.filter(
            servidores__in=servidores,
            data_ida__lte=atividade.data_retorno,
            data_retorno__gte=atividade.data_ida
        ).exclude(id=atividade.id).exclude(agendamento__status="cancelado")
        for a in conflitos:
            for servidor in a.servidores.all():
                servidores_conflito_ids.add(servidor.id)

    # Monta lista de servidores com flag de motorista
    servidores_status = []
    for servidor in servidores:
        em_conflito = servidor.id in servidores_conflito_ids
        eh_motorista = getattr(servidor, "eh_motorista", False)  # campo booleano no modelo Servidor
        servidores_status.append({
            "servidor": servidor,
            "em_conflito": em_conflito,
            "eh_motorista": eh_motorista
        })
    ocultar_diarias = False
    if atividade and atividade.municipio:
        municipios_sem_diarias = [
            "Belém", "Ananindeua", "Benevides", "Marituba",
            "Santa Bárbara do Pará", "Santa Isabel do Pará",
            "Castanhal", "Barcarena"
        ]
        # normaliza toda a lista
        municipios_sem_diarias = [normalizar(m) for m in municipios_sem_diarias]

        # normaliza o valor selecionado
        municipio_normalizado = normalizar(atividade.municipio)

        if municipio_normalizado in municipios_sem_diarias:
            ocultar_diarias = True

        # se o município tiver qualquer parte igual a um dos nomes da lista, ele já oculta
        #if any(m in municipio_normalizado for m in municipios_sem_diarias):
    return render(request, "atividades/editar_atividade.html", {
        "atividade": atividade,
        "servidores_status": servidores_status,
        "setores": setores,
        "motoristas_externos": motoristas_externos,
        "ocultar_diarias": ocultar_diarias,
        "transporte_choices": transporte_choices,
    })


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
    servidor_nome = request.GET.get("servidor_nome") or ""

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
    if servidor_nome:
        atividades = atividades.filter(servidores__nome__icontains=servidor_nome).distinct()

    # Paginação
    paginator = Paginator(atividades, 10)  # 10 registros por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Adiciona periodo_formatado em cada atividade
    for atividade in page_obj:
        atividade.periodo_formatado = formatar_periodo(atividade.data_ida, atividade.data_retorno)

    return render(request, "atividades/listar_atividades.html", {
        # passa para template
        "page_obj": page_obj,
        "municipio": municipio,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "servidor_nome": servidor_nome,
        "recurso_ativo": recurso_ativo,
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

    # Garante que os dois tipos existam
    ValorDiaria.objects.get_or_create(tipo="PARA", defaults={"valor": 0})
    ValorDiaria.objects.get_or_create(tipo="OUTROS", defaults={"valor": 0})

    valores = ValorDiaria.objects.all()
    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "recurso":
            codigo = request.POST.get("recurso")
            recurso_ativo.codigo = codigo
            recurso_ativo.save()
            messages.success(request, f"Recurso alterado para {codigo}")
            return redirect("definir_recurso")
        
        elif acao == "valor":
            for v in ValorDiaria.objects.all():
                novo_valor = request.POST.get(f"valor_{v.tipo}")
                if novo_valor:
                    v.valor = novo_valor
                    v.save()
            messages.success(request, "Valores de diárias atualizados com sucesso.")
            return redirect("definir_recurso")

    return render(request, "setores/cadastrar_setor.html", {
        "recurso_ativo": recurso_ativo, 
        "setores": Setor.objects.all(), 
        "valores": valores,
        })

def gerar_dias_mes(ano, mes):
    dias_semana = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
    dias_mes = []
    dias_especiais = DiaEspecial.objects.filter(data__year=ano, data__month=mes)

    especiais_dict = {d.data: d for d in dias_especiais}
    for dia in range(1, calendar.monthrange(ano, mes)[1] + 1):
        data = date(ano, mes, dia)
        semana = dias_semana[data.weekday()]
        especial = especiais_dict.get(data)
        dias_mes.append((dia, semana, especial))
    return dias_mes

@login_required(login_url='/login/')
def gerar_folha_ponto(request):
    setores = Setor.objects.all()
    servidores = Servidor.objects.all()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    dias_mes_atual = gerar_dias_mes(ano_atual, mes_atual)
    MESES_PT = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    nome_mes_atual = MESES_PT[mes_atual - 1]

    # pega setores selecionados via GET
    setores_ids = request.GET.getlist("setores")
    
    if request.method == "POST":
        ids = request.POST.getlist("servidores")
        servidores_selecionados = servidores.filter(id__in=ids)

        meses_selecionados = request.POST.getlist("meses")
        if meses_selecionados:
            meses_selecionados = [int(m) for m in meses_selecionados]
        else:
            meses_selecionados = [mes_atual]  # se não selecionar, usa o mês atual


        html_total = ""
        
        for servidor in servidores_selecionados:
            for mes in meses_selecionados:
                dias_mes = gerar_dias_mes(ano_atual, mes)
                nome_mes = MESES_PT[mes - 1]

                situacao = servidor.historico_situacoes.last()
                html = render_to_string("pdf_folha_ponto.html", {
                    "servidor": servidor,
                    "situacao": situacao,
                    "dias_mes": dias_mes,
                    "mes_atual": nome_mes,
                    "ano_atual": ano_atual,
                })
                # adiciona quebra de página entre folhas
                html_total += html + '<div style="page-break-after: always;"></div>'

        # gera um único PDF com todas as folhas
        pdf_bytes = HTML(string=html_total).write_pdf()


        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="folhas_ponto_{ano_atual}.pdf"'
        return response

    meses = [(i, MESES_PT[i - 1]) for i in range(1, 13)]
    return render(request, "atividades/cadastro_folha_ponto.html", {
        "servidores": servidores,
        "setores": setores,
        "setores_ids": setores_ids,
        "dias_mes": dias_mes_atual,
        "mes_atual": nome_mes_atual,
        "ano_atual": ano_atual,
        "meses": meses,
    })


@login_required(login_url='/login/')
def cadastrar_dia_especial(request):
    if request.method == "POST":
        data_str = request.POST.get("data")
        if data_str:
            data = datetime.strptime(data_str, "%Y-%m-%d").date()
        tipo = request.POST.get("tipo")
        nome = request.POST.get("nome")

        if data and tipo:
            DiaEspecial.objects.get_or_create(
                data=data,
                defaults={"tipo": tipo, "nome": nome}
            )
            messages.success(request, "Dia especial cadastrado com sucesso!")
            return redirect("cadastrar_dia_especial")

    dias_especiais = DiaEspecial.objects.all()
    return render(request, "atividades/cadastrar_dia_especial.html", {"dias_especiais": dias_especiais})

@login_required(login_url='/login/')
def gerar_folha_plantao(request):
    setores = Setor.objects.all()
    servidores = Servidor.objects.all()
    ano_atual = datetime.now().year
    mes_atual = datetime.now().month
    dias_mes = gerar_dias_mes(ano_atual, mes_atual)
    # Nome do mês em português
    nome_mes = datetime.now().strftime("%B").capitalize()

    # pega setores selecionados via GET
    setores_ids = request.GET.getlist("setores")
    
    if request.method == "POST":
        ids = request.POST.getlist("servidores")
        servidores_selecionados = Servidor.objects.filter(id__in=ids)

        buffer = io.BytesIO()
        html_total = ""

        for servidor in servidores_selecionados:
            html = render_to_string("pdf_folha_plantao.html", {
                "servidor": servidor,
                "dias_mes": dias_mes,
                "mes_atual": nome_mes,
                "ano_atual": ano_atual,
            })
            # adiciona quebra de página entre servidores
            html_total += html + '<div style="page-break-after: always;"></div>'

        # gera um único PDF com todas as folhas
        pdf_bytes = HTML(string=html_total).write_pdf()

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="folhas_plantoes_{nome_mes}_{ano_atual}.pdf"'
        return response

    return render(request, "atividades/cadastro_folha_plantao.html", {
        "servidores": servidores,
        "setores": setores,
        "setores_ids": setores_ids,  # passa para o template
        "dias_mes": dias_mes,
        "mes_atual": nome_mes,
        "ano_atual": ano_atual,
    })

@login_required(login_url='/login/')
def prestar_contas(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)
    servidores = atividade.servidores.all()
    setores = Setor.objects.all()
    prestacao = atividade


    # --- Lógica de setores igual ao pdf_atividade ---
    setores = Setor.objects.filter(nome__startswith="DEVS")
    setor_dvs = Setor.objects.filter(nome__startswith="DVS")

    # Verifica se o chefe imediato está entre os servidores
    chefe_matricula = atividade.chefe_imediato.matricula_chefe if atividade.chefe_imediato else None
    chefe_eh_servidor = False
    if chefe_matricula:
        chefe_eh_servidor = servidores.filter(matricula=chefe_matricula).exists()

    setores_filtrados = []
    for setor in setores:
        if not servidores.filter(matricula=setor.matricula_chefe).exists():
            setores_filtrados.append(setor)
        else:
            setores_filtrados.extend(setor_dvs)
    # --- Seleção do chefe da autoridade ---
    setor_devs = Setor.objects.filter(nome="DEVS/DVS/SESPA").first()
    

    chefe_setor = None
    if setor_devs:
        chefe_setor = setor_devs
        # Se algum servidor tem a mesma matrícula do chefe DEVS/DVS/SESPA,
        # então usa o chefe imediato do setor do servidor
        for servidor in servidores:
            if servidor.matricula == setor_devs.matricula_chefe and servidor.setor:
                # pega o chefe imediato do setor do servidor
                chefe_setor = servidor.setor
                break
    # --- cálculo das diárias ---
    dias_diarias_str = atividade.dias_diarias  # exemplo: "2 / 1,5"

    # Quebra a string em duas partes
    partes = dias_diarias_str.split("/")

    # Pega a parte depois da barra, remove espaços e troca vírgula por ponto
    valor_str = partes[1].strip().replace(",", ".")

    # Converte para float
    valor_float = float(valor_str)

    # Para viagem dentro do Pará
    valor_para = ValorDiaria.objects.get(tipo="PARA").valor

    # Para viagem para outros estados
    valor_outros = ValorDiaria.objects.get(tipo="OUTROS").valor

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # 1. Para cada servidor, gerar um PDF de prestação de contas/Relatório de Viagem
        for servidor in servidores:
            motorista_servidor = None
            for servidor in servidores:
                if getattr(servidor, "eh_motorista", False):
                    motorista_servidor = servidor
                    break
            html_relatorio = render_to_string("pdf_prestacao_contas.html", {
                "atividade": atividade,
                "servidores": [servidor],
                "motoristas_externos": atividade.motoristas_externos.all(),
                "motorista_servidor": motorista_servidor,  # passa o motorista servidor
                "setores": setores,
                "periodo_formatado": formatar_periodo(atividade.data_ida, atividade.data_retorno),
                "valor_unitario": valor_para,
                "valor_total": round(float(valor_float or 0) * float(valor_para), 2),
                "diarias":valor_float,
                "prestacao": prestacao,  # passa os dados da prestação
                "chefe_setor": chefe_setor,  # passa o chefe correto para o template
            })
            pdf_relatorio = HTML(string=html_relatorio, base_url=request.build_absolute_uri('/')).write_pdf()
            zip_file.writestr(f"relatorio_viagem_{servidor.primeiro_e_ultimo_nome()}_{atividade.id}.pdf", pdf_relatorio)

        # 2. PDF Memorando
        html_memorando = render_to_string("pdf_memorando_prestacao_contas.html", {
            "atividade": atividade,
            "servidores": servidores,
            "setores": setores_filtrados,
            "chefe_eh_servidor": False,  # ajuste conforme sua lógica
            "chefe_setor": chefe_setor,
        })
        pdf_memorando = HTML(string=html_memorando, base_url=request.build_absolute_uri('/')).write_pdf()
        zip_file.writestr(f"memorando_{atividade.id}.pdf", pdf_memorando)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response['Content-Disposition'] = f'attachment; filename="prestacao_contas_{atividade.id}.zip"'
    return response


@login_required(login_url='/login/')
def prestar_contas_form(request, atividade_id):
    atividade = get_object_or_404(Atividade, id=atividade_id)
    veiculos = Veiculo.objects.all().order_by("modelo")
    
    if request.method == "POST":
        atividade.portaria_numero = request.POST.get("portaria_numero")
        atividade.data_prestacao = request.POST.get("data")
        atividade.objetivo_prestacao = request.POST.get("objetivo")
        atividade.observacao_prestacao = request.POST.get("observacao")
        veiculo_id = request.POST.get("veiculo")
        atividade.veiculo_prestacao = Veiculo.objects.get(id=veiculo_id) if veiculo_id else None
        atividade.horario_partida = request.POST.get("horario_partida")
        atividade.horario_guarda = request.POST.get("horario_guarda")
        atividade.devolucao = request.POST.get("devolucao")
        # Captura anexos e sequenciais
        anexos_selecionados = request.POST.getlist("anexos")
        anexos_dict = {}
        for anexo in anexos_selecionados:
            seq_valor = request.POST.get(f"seq_{anexo}")
            anexos_dict[anexo] = int(seq_valor) if seq_valor else None

        atividade.anexos = anexos_dict
        # Campos bancários
        atividade.cnpj = request.POST.get("cnpj")
        atividade.banco = request.POST.get("banco")
        atividade.agencia = request.POST.get("agencia")
        atividade.conta_corrente = request.POST.get("conta_corrente")
        
        atividade.save()
        messages.success(request, "Prestação de contas registrada com sucesso!")
        return redirect("listar_atividades")
    numeros = range(1, 11)
    return render(request, "atividades/prestar_contas_form.html", {
        "atividade": atividade,
        "veiculos": veiculos,
        "numeros": numeros,
    })
