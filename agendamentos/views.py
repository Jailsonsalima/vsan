from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .forms import AgendamentoForm, ProcessamentoAgendamentoForm, MotoristaExternoForm
from django.contrib import messages
from .models import Agendamento, AutorizacaoAgendamento, MotoristaExterno, ProcessamentoAgendamento
from usuarios.models import Usuario
from servidores.models import Servidor
from django.utils import timezone
from django.db.models import Q, Count

from django.core.paginator import Paginator
import calendar
import json
import locale
import calendar
from setores.models import Setor
from datetime import datetime, date
from django.utils.dateformat import DateFormat

from django.template.loader import render_to_string
from weasyprint import HTML

from django.http import HttpResponse

def formatar_periodo(data_ida, data_retorno):
    if not data_ida or not data_retorno:
        return ""
    if data_ida.month == data_retorno.month and data_ida.year == data_retorno.year:
        return f"{data_ida.day} a {data_retorno.day}/{data_ida.month:02d}/{data_ida.year}"
    else:
        return f"{DateFormat(data_ida).format('d/m/Y')} a {DateFormat(data_retorno).format('d/m/Y')}"
    
@login_required(login_url='/login/')
def solicitar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.solicitante = request.user
            if not request.user.servidor:
                messages.error(request, "Seu usuário não está vinculado a um servidor. Contate o administrador.")
                return redirect('home')
            agendamento.servidor = request.user.servidor
            # Verificação de duplicidade
            existe = Agendamento.objects.filter(
                solicitante=request.user,
                data_ida=agendamento.data_ida,
                data_retorno=agendamento.data_retorno,
                municipio=agendamento.municipio,
                motivo=agendamento.motivo,
                transporte=agendamento.transporte,
                status__in=["pendente", "processado"]  # só bloqueia se ainda ativo
            ).exists()

            if existe:
                messages.error(request, "Já existe uma solicitação idêntica registrada. Evite duplicidade.")
                return redirect('listar_agendamentos')

            # Se não existir duplicado, prossegue normalmente
            agendamento.save()
            necessita_motorista = request.POST.get("necessita_motorista")
            if agendamento.transporte == "Veículo Oficial (VAN)" or agendamento.transporte == "Veículo Oficial" or (agendamento.transporte in ["Fluvial", "Aéreo"] and necessita_motorista == "sim"):
                # Sorteio de motorista
                # Verifica motoristas internos disponíveis
                motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista", disponivel=True)
                motoristas_ocupados = ProcessamentoAgendamento.objects.filter(
                    agendamento__data_ida__lte=agendamento.data_retorno,
                    agendamento__data_retorno__gte=agendamento.data_ida,
                    agendamento__status="processado" # só considera ocupado os com status processado
                ).values_list("motorista_servidor_id", flat=True)

                motoristas_disponiveis = motoristas_servidores.exclude(id__in=motoristas_ocupados)

                if motoristas_disponiveis.exists():
                    # Sorteia motorista com menor tempo desde última vez
                    motorista_sorteado = motoristas_disponiveis.order_by('ultima_vez_sorteado').first()

                    processamento = ProcessamentoAgendamento.objects.create(
                        agendamento=agendamento,
                        tipo="Da Vigilância",
                        motorista_servidor=motorista_sorteado
                    )

                    motorista_sorteado.ultima_vez_sorteado = timezone.now()
                    motorista_sorteado.save()

                    agendamento.status = "processado"
                    agendamento.save()
                    messages.success(request, "O primeiro passo foi concluído!")
                    messages.info(request, f"Agora, complete os campos do formulário a baixo.")

                    if agendamento.transporte == "Veículo Oficial (VAN)":
                        # Envia e-mail aos autorizados
                        autorizados = AutorizacaoAgendamento.objects.filter(pode_visualizar=True)
                        for autorizacao in autorizados:
                            send_mail(
                                'Agendamento de VAN',
                                f'Um novo agendamento de uma VAN foi solicitado e está aguardando.\nDados: {agendamento}',
                                'sistema@vsan.com',
                                [autorizacao.usuario.email]
                            )

                    return redirect('cadastrar_atividade_agendamento', agendamento_id=agendamento.id)
                # Não há motorista interno disponível
                else:
                    # Não há motorista interno disponível com VAN
                    if agendamento.transporte == "Veículo Oficial (VAN)":
                        messages.info(request, "Não há motorista da Vigilância disponível.\n Aguarde designação de motorista externo e da VAN.")

                        # Envia e-mail aos autorizados
                        autorizados = AutorizacaoAgendamento.objects.filter(pode_visualizar=True)
                        for autorizacao in autorizados:
                            send_mail(
                                'Agendamento aguardando motorista externo e VAN',
                                f'Um novo agendamento foi solicitado e está aguardando motorista externo e uma VAN.\nDados: {agendamento}',
                                'sistema@vsan.com',
                                [autorizacao.usuario.email]
                            )
                        send_mail(
                            'Agendamento aguardando motorista externo e VAN',
                            f'Sua solicitação foi registrada. Aguarde confirmação.\n\n'
                            f'Dados do agendamento:\n'
                            f'Ida: {agendamento.data_ida.strftime("%d/%m/%Y")}\n'
                            f'Retorno: {agendamento.data_retorno.strftime("%d/%m/%Y")}\n'
                            f'Transporte {agendamento.transporte}\n'
                            f'Município: {agendamento.municipio}\n'
                            f'Motivo: {agendamento.motivo}',
                            'sistema@vsan.com',
                            [request.user.email]
                        )
                    else:
                        # Não há motorista interno disponível
                        messages.info(request, "Não há motorista da Vigilância disponível.\n Aguarde designação de motorista externo.")

                        # Envia e-mail ao solicitante
                        send_mail(
                            'Agendamento aguardando motorista externo',
                            f'Sua solicitação foi registrada. Aguarde confirmação.\n\n'
                            f'Dados do agendamento:\n'
                            f'Ida: {agendamento.data_ida.strftime("%d/%m/%Y")}\n'
                            f'Retorno: {agendamento.data_retorno.strftime("%d/%m/%Y")}\n'
                            f'Transporte {agendamento.transporte}\n'
                            f'Município: {agendamento.municipio}\n'
                            f'Motivo: {agendamento.motivo}',
                            'sistema@vsan.com',
                            [request.user.email]
                        )

                        # Envia e-mail aos autorizados
                        autorizados = AutorizacaoAgendamento.objects.filter(pode_visualizar=True)
                        for autorizacao in autorizados:
                            send_mail(
                                'Agendamento aguardando motorista externo',
                                f'Um novo agendamento foi solicitado e está aguardando motorista externo.\nDados: {agendamento}',
                                'sistema@vsan.com',
                                [autorizacao.usuario.email]
                            )

                    return redirect('listar_agendamentos')
            else:
                if agendamento.transporte != "Veículo Oficial (VAN)" and agendamento.transporte != "Veículo Oficial" and necessita_motorista == "nao":
                    agendamento.status = "processado"
                    agendamento.save()
                # Não sorteia motorista
                messages.success(request, f"Agendamento registrado com transporte: {agendamento.transporte}")
                messages.info(request, f"Agora, complete os outros campos do formulário.")
                return redirect('cadastrar_atividade_agendamento', agendamento_id=agendamento.id)
        else:
            form = AgendamentoForm()
    else:
        form = AgendamentoForm()
    return render(request, 'agendamentos/solicitar.html', {'form': form})


@login_required(login_url='/login/')
def gerenciar_autorizacoes(request):
    if request.user.tipo_usuario != 'diretor':
        messages.error(request, "Apenas diretores podem gerenciar autorizações.")
        return redirect('dashboard')

    usuarios = Usuario.objects.filter(is_superuser=False).exclude(id=request.user.id)

    # Filtro por nome (username OU nome do servidor vinculado)
    filtro_nome = request.GET.get("nome") or ""
    if filtro_nome:
        usuarios = usuarios.filter(
            Q(username__icontains=filtro_nome) |
            Q(servidor__nome__icontains=filtro_nome)
        )

    # Paginação
    paginator = Paginator(usuarios, 10)  # 10 usuários por página
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # garante que cada usuário tenha um objeto de autorização
    for usuario in page_obj:
        autorizacao, _ = AutorizacaoAgendamento.objects.get_or_create(usuario=usuario)
        usuario.autorizacao = autorizacao

    motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista")
    motoristas_externos = MotoristaExterno.objects.all()

    if request.method == 'POST':
        for usuario in page_obj:
            visualizar = request.POST.get(f"visualizar_{usuario.id}") == "on"
            processar = request.POST.get(f"processar_{usuario.id}") == "on"
            autorizacao, _ = AutorizacaoAgendamento.objects.get_or_create(usuario=usuario)
            usuario.autorizacao.pode_visualizar = visualizar
            usuario.autorizacao.pode_processar = processar
            usuario.autorizacao.save()
        messages.success(request, "Autorizações de usuários atualizadas com sucesso.")
        return redirect('gerenciar_autorizacoes')

    return render(request, 'agendamentos/gerenciar_autorizacoes.html', {
        'page_obj': page_obj,
        'motoristas_servidores': motoristas_servidores,
        'motoristas_externos': motoristas_externos,
        'filtro_nome': filtro_nome,
    })


@login_required(login_url='/login/')
def processar_agendamento(request, agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)

    # Verifica permissão
    autorizacao = AutorizacaoAgendamento.objects.filter(usuario=request.user, pode_visualizar=True).first()
    autorizado = bool(autorizacao or request.user.tipo_usuario == "diretor")

    # Impede reprocessamento
    if agendamento.status == "processado" or ProcessamentoAgendamento.objects.filter(agendamento=agendamento).exists():
        messages.error(request, "Este agendamento já foi processado e não pode ser alterado novamente.")
        return redirect('listar_agendamentos')

    # Motoristas disponíveis
    motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista")
    motoristas_externos = MotoristaExterno.objects.all()

    motoristas_servidores_disponiveis = motoristas_servidores.filter(disponivel=True).exclude(
        id__in=ProcessamentoAgendamento.objects.filter(
            motorista_servidor__in=motoristas_servidores,
            agendamento__data_ida__lte=agendamento.data_retorno,
            agendamento__data_retorno__gte=agendamento.data_ida
        ).values_list("motorista_servidor_id", flat=True)
    )

    motoristas_externos_disponiveis = motoristas_externos.filter(disponivel=True).exclude(
        id__in=ProcessamentoAgendamento.objects.filter(
            motorista_externo__in=motoristas_externos,
            agendamento__data_ida__lte=agendamento.data_retorno,
            agendamento__data_retorno__gte=agendamento.data_ida
        ).values_list("motorista_externo_id", flat=True)
    )

    motorista_sorteado = None
    aviso_motorista = None

    if request.method == 'POST':
        form = ProcessamentoAgendamentoForm(request.POST)
        if form.is_valid():
            processamento = form.save(commit=False)
            processamento.agendamento = agendamento

            if processamento.tipo == "Da Vigilância":
                if motoristas_servidores_disponiveis:
                    # Sorteia o motorista com menor tempo desde última vez
                    # Seleciona o motorista com a data mais antiga (ou nula)
                    motorista_sorteado = motoristas_servidores_disponiveis.order_by('ultima_vez_sorteado').first()
                    processamento.motorista_servidor = motorista_sorteado
                    motorista_sorteado.ultima_vez_sorteado = timezone.now()
                    motorista_sorteado.save()
                else:
                    messages.error(request, "Não há motorista disponível da Vigilância. Selecione um motorista externo.")
                    return render(request, 'agendamentos/processar.html', {
                        'form': form,
                        'agendamento': agendamento,
                        'motorista_sorteado': None,
                        'aviso_motorista': "Não há motorista disponível da Vigilância. Selecione um motorista externo.",
                        "autorizado": autorizado,
                    })

            elif processamento.tipo == "outros":
                if not processamento.motorista_externo:
                    messages.error(request, "Você deve selecionar um motorista externo para continuar.")
                    return render(request, 'agendamentos/processar.html', {
                        'form': form,
                        'agendamento': agendamento,
                        'motorista_sorteado': None,
                        'aviso_motorista': "Selecione um motorista externo para processar o agendamento."
                    })

            processamento.save()
            agendamento.status = "processado"
            agendamento.save()

            # E-mail ao solicitante
            motorista_nome = None
            motorista_telefone = None
            if processamento.motorista_servidor:
                motorista_nome = processamento.motorista_servidor.nome
                motorista_telefone = getattr(processamento.motorista_servidor, "telefone", None)
            elif processamento.motorista_externo:
                motorista_nome = processamento.motorista_externo.nome
                motorista_telefone = processamento.motorista_externo.telefone

            send_mail(
                'Agendamento Processado',
                f'Sua solicitação foi respondida.\n\n'
                f'Dados do agendamento:\n'
                f'Ida: {agendamento.data_ida.strftime("%d/%m/%Y")}\n'
                f'Retorno: {agendamento.data_retorno.strftime("%d/%m/%Y")}\n'
                f'Município: {agendamento.municipio}\n'
                f'Motivo: {agendamento.motivo}\n\n'
                f'Motorista designado: {motorista_nome or "Não informado"}\n'
                f'Telefone: {motorista_telefone or "Não informado"}',
                'sistema@vsan.com',
                [agendamento.solicitante.email],
            )

            messages.success(request, "Agendamento processado com sucesso.")
            return redirect('listar_agendamentos')
    else:
        form = ProcessamentoAgendamentoForm()
        form.fields["motorista_servidor"].queryset = motoristas_servidores_disponiveis
        form.fields["motorista_servidor"].widget.attrs["disabled"] = True
        form.fields["motorista_externo"].queryset = motoristas_externos_disponiveis

        # Sorteia no GET e guarda na sessão
        if motoristas_servidores_disponiveis:
            motorista_sorteado = motoristas_servidores_disponiveis.order_by('ultima_vez_sorteado').first()
        else:
            aviso_motorista = "Não há motorista disponível da Vigilância. Selecione um motorista externo."

    return render(request, 'agendamentos/processar.html', {
        'form': form,
        'agendamento': agendamento,
        'motorista_sorteado': motorista_sorteado,
        'aviso_motorista': aviso_motorista,
        "autorizado": autorizado,
    })

# Define locale para português do Brasil
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

@login_required(login_url='/login/')
def listar_agendamentos(request):
    usuario = request.user
    # Apenas usuários autorizados podem visualizar
    autorizacao = AutorizacaoAgendamento.objects.filter(usuario=request.user, pode_visualizar=True).first()
    autorizado = bool(autorizacao or usuario.tipo_usuario == "diretor")
    # if not autorizacao and request.user.tipo_usuario != 'diretor':
    #     messages.error(request, "Você não tem permissão para visualizar os agendamentos.")
    #     return render(request, "usuarios/dashboard.html")
    # Se for diretor, vê todos
    if usuario.tipo_usuario == "diretor" or autorizacao:
        agendamentos = Agendamento.objects.all().order_by("-data_solicitacao").select_related("processamento")
    else:
        # Solicitações feitas pelo próprio usuário
        meus_agendamentos = Agendamento.objects.filter(solicitante=usuario)

        # Solicitações dos servidores cujo chefe imediato é o mesmo setor do usuário
        chefe_setor = usuario.servidor.setor if hasattr(usuario, "servidor") and usuario.servidor else None
        subordinados_agendamentos = Agendamento.objects.filter(servidor__setor=chefe_setor) if chefe_setor else Agendamento.objects.none()
        # Junta os dois conjuntos
        agendamentos = (meus_agendamentos | subordinados_agendamentos).order_by("-data_solicitacao").select_related("processamento")
    # Filtro por município
    filtro_municipio = request.GET.get("municipio") or ""
    if filtro_municipio:
        agendamentos = agendamentos.filter(municipio__icontains=filtro_municipio)
    # Busca todos os agendamentos
    #agendamentos = Agendamento.objects.all().order_by("-data_solicitacao").select_related("processamento")  

    # Paginação
    paginator = Paginator(agendamentos, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    # Adiciona periodo_formatado em cada agendamento
    for agendamento in page_obj:
        agendamento.periodo_formatado = formatar_periodo(agendamento.data_ida, agendamento.data_retorno)

    motoristas = Servidor.objects.filter(cargo__icontains="Motorista")
    motorista_id = request.GET.get("motorista")
    motorista = None

    ano = int(request.GET.get("ano", timezone.now().year))
    mes = int(request.GET.get("mes", timezone.now().month))

    # Paleta de cores fixa (mesma usada nos gráficos)
    paleta = ['#f44336','#2196f3','#4caf50','#ff9800','#9c27b0','#00bcd4']
    dias_por_motorista = {}

    if motorista_id:
        # modo individual

        try:
            motorista = Servidor.objects.get(id=motorista_id)
            agendamentos_motorista = ProcessamentoAgendamento.objects.filter(motorista_servidor=motorista)
            dias_por_motorista[motorista.id] = {"nome": motorista.nome, "dias": [], "cor": paleta[0]}
            for ag in agendamentos_motorista:
                if ag.agendamento.data_ida.month == mes and ag.agendamento.data_ida.year == ano:
                    dias_por_motorista[motorista.id]["dias"].extend(
                        range(ag.agendamento.data_ida.day, ag.agendamento.data_retorno.day + 1)
                    )
        except Servidor.DoesNotExist:
            motorista = None
    else:
        # modo todos juntos
        for i, m in enumerate(motoristas):
            agendamentos_motorista = ProcessamentoAgendamento.objects.filter(motorista_servidor=m)
            dias_por_motorista[m.id] = {"nome": m.nome, "dias": [], "cor": paleta[i % len(paleta)]}
            for ag in agendamentos_motorista:
                if ag.agendamento.data_ida.month == mes and ag.agendamento.data_ida.year == ano:
                    dias_por_motorista[m.id]["dias"].extend(
                        range(ag.agendamento.data_ida.day, ag.agendamento.data_retorno.day + 1)
                    )
    # número de agendamentos por motorista no mês/ano atual
    dados_motoristas_query = ProcessamentoAgendamento.objects.filter(
        agendamento__data_ida__month=mes,
        agendamento__data_ida__year=ano,
        motorista_servidor__isnull=False
    )
    # Se um motorista foi selecionado, filtra apenas ele
    if motorista_id:
        dados_motoristas_query = dados_motoristas_query.filter(motorista_servidor_id=motorista_id)

    dados_motoristas = (
        dados_motoristas_query
        .values("motorista_servidor__id", "motorista_servidor__nome")
        .annotate(total=Count("id"))
        .order_by("motorista_servidor__nome")
    )
    # número de dias em viagem por motorista no mês/ano atual
    dados_dias_motoristas = []
    motoristas_ids = dados_motoristas_query.values_list("motorista_servidor__id", flat=True).distinct()
    for mid in motoristas_ids:
        try:
            motorista_obj = Servidor.objects.get(id=mid)
        except Servidor.DoesNotExist:
            continue
        ags = ProcessamentoAgendamento.objects.filter(
            motorista_servidor_id=mid,
            agendamento__data_ida__month=mes,
            agendamento__data_ida__year=ano
        )
        total_dias = sum((ag.agendamento.data_retorno - ag.agendamento.data_ida).days + 1 for ag in ags)
        dados_dias_motoristas.append({
            "motorista_servidor__id": mid,
            "motorista_servidor__nome": motorista_obj.nome,
            "total_dias": total_dias
        })

    cal = calendar.Calendar(firstweekday=6)
    dias_mes = cal.monthdayscalendar(ano, mes)

    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = mes + 1 if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1
    nome_mes = calendar.month_name[mes].capitalize()

    return render(request, "agendamentos/listar.html", {
        "motoristas": motoristas,
        "motorista_selecionado": motorista,
        "dias_por_motorista": dias_por_motorista,
        "dias_mes": dias_mes,
        "mes": mes,
        "ano": ano,
        "nome_mes": nome_mes,
        "mes_anterior": mes_anterior,
        "ano_anterior": ano_anterior,
        "mes_proximo": mes_proximo,
        "ano_proximo": ano_proximo,
        "dados_motoristas": json.dumps(list(dados_motoristas)),
        "dados_dias_motoristas": json.dumps(list(dados_dias_motoristas)),
        "agendamentos": agendamentos,
        "page_obj": page_obj,
        "filtro_municipio": filtro_municipio,
        "autorizado": autorizado,
    })
    
@login_required(login_url='/login/')
def gerenciar_motoristas(request):
    if request.user.tipo_usuario != 'diretor':
        messages.error(request, "Apenas diretores podem gerenciar motoristas.")
        return redirect('dashboard')

    motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista")
    motoristas_externos = MotoristaExterno.objects.all()

    if request.method == 'POST':
        # Atualiza disponibilidade dos motoristas internos
        for motorista in motoristas_servidores:
            disponivel = request.POST.get(f"motorista_servidor_{motorista.id}") == "on"
            motorista.disponivel = disponivel
            motorista.save()

        # Atualiza disponibilidade dos motoristas externos
        for motorista in motoristas_externos:
            disponivel = request.POST.get(f"motorista_externo_{motorista.id}") == "on"
            motorista.disponivel = disponivel
            motorista.save()

        messages.success(request, "Motoristas atualizados com sucesso.")
        return redirect('gerenciar_motoristas')

    return render(request, 'agendamentos/gerenciar_autorizacoes.html', {
        'usuarios': Usuario.objects.filter(is_superuser=False).exclude(id=request.user.id),
        'motoristas_servidores': motoristas_servidores,
        'motoristas_externos': motoristas_externos,
    })

@login_required(login_url='/login/')
def cadastrar_motorista_externo(request):
    setores = Setor.objects.all()
    if request.method == 'POST':
        setor_id = request.POST.get("setor")
        setor = Setor.objects.get(id=setor_id) if setor_id else None
        form = MotoristaExternoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Motorista externo cadastrado com sucesso.")
            return redirect('listar_agendamentos')
    else:
        form = MotoristaExternoForm()

    return render(request, 'agendamentos/motorista_externo_form.html', {'form': form, "setores": setores})

@login_required(login_url='/login/')
def adicionar_processo(request, agendamento_id):
    processamento = ProcessamentoAgendamento.objects.filter(agendamento_id=agendamento_id).first()
    if not processamento:
        messages.error(request, "Este agendamento não possui processamento registrado.")
        return redirect('listar_agendamentos')

    if request.method == "POST":
        numero = request.POST.get("numero_processo")
        processamento.numero_processo = numero
        processamento.save()
        messages.success(request, "Número do processo adicionado com sucesso.")
        return redirect('listar_agendamentos')
    return render(request, "agendamentos/adicionar_processo.html", {"processamento": processamento})


@login_required(login_url='/login/')
def calendario_motorista(request):
    motoristas = Servidor.objects.filter(cargo__icontains="Motorista")

    motorista_id = request.GET.get("motorista")
    motorista = None

    ano = int(request.GET.get("ano", timezone.now().year))
    mes = int(request.GET.get("mes", timezone.now().month))

    # Paleta de cores fixa (mesma usada nos gráficos)
    paleta = ['#f44336','#2196f3','#4caf50','#ff9800','#9c27b0','#00bcd4']

    dias_por_motorista = {}

    if motorista_id:
        # modo individual
        try:
            motorista = Servidor.objects.get(id=motorista_id)
            agendamentos = ProcessamentoAgendamento.objects.filter(motorista_servidor=motorista)
            dias_por_motorista[motorista.id] = {
                "nome": motorista.nome,
                "dias": [],
                "cor": paleta[0]  # cor fixa para o selecionado
            }
            for ag in agendamentos:
                if ag.agendamento.data_ida.month == mes and ag.agendamento.data_ida.year == ano:
                    dias_por_motorista[motorista.id]["dias"].extend(
                        range(ag.agendamento.data_ida.day, ag.agendamento.data_retorno.day + 1)
                    )
        except Servidor.DoesNotExist:
            motorista = None
    else:
        # modo todos juntos
        for i, m in enumerate(motoristas):
            agendamentos = ProcessamentoAgendamento.objects.filter(motorista_servidor=m)
            dias_por_motorista[m.id] = {
                "nome": m.nome,
                "dias": [],
                "cor": paleta[i % len(paleta)]  # cor cíclica
            }
            for ag in agendamentos:
                if ag.agendamento.data_ida.month == mes and ag.agendamento.data_ida.year == ano:
                    dias_por_motorista[m.id]["dias"].extend(
                        range(ag.agendamento.data_ida.day, ag.agendamento.data_retorno.day + 1)
                    )

    # número de agendamentos por motorista no mês/ano atual
    dados_motoristas_query = ProcessamentoAgendamento.objects.filter(
        agendamento__data_ida__month=mes,
        agendamento__data_ida__year=ano,
        motorista_servidor__isnull=False
    )

    # Se um motorista foi selecionado, filtra apenas ele
    if motorista_id:
        dados_motoristas_query = dados_motoristas_query.filter(motorista_servidor_id=motorista_id)

    dados_motoristas = (
        dados_motoristas_query
        .values("motorista_servidor__id", "motorista_servidor__nome")
        .annotate(total=Count("id"))
        .order_by("motorista_servidor__nome")
    )

    # número de dias em viagem por motorista no mês/ano atual
    dados_dias_motoristas = []
    motoristas_ids = dados_motoristas_query.values_list("motorista_servidor__id", flat=True).distinct()

    for mid in motoristas_ids:
        try:
            motorista_obj = Servidor.objects.get(id=mid)
        except Servidor.DoesNotExist:
            continue
        agendamentos = ProcessamentoAgendamento.objects.filter(
            motorista_servidor_id=mid,
            agendamento__data_ida__month=mes,
            agendamento__data_ida__year=ano
        )
        total_dias = sum(
            (ag.agendamento.data_retorno - ag.agendamento.data_ida).days + 1
            for ag in agendamentos
        )
        dados_dias_motoristas.append({
            "motorista_servidor__id": mid,
            "motorista_servidor__nome": motorista_obj.nome,
            "total_dias": total_dias
        })

    cal = calendar.Calendar(firstweekday=6)
    dias_mes = cal.monthdayscalendar(ano, mes)

    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = mes + 1 if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1
    nome_mes = calendar.month_name[mes].capitalize()

    return render(request, "agendamentos/calendario_motorista.html", {
        "motoristas": motoristas,
        "motorista_selecionado": motorista,
        "dias_por_motorista": dias_por_motorista,
        "dias_mes": dias_mes,
        "mes": mes,
        "ano": ano,
        "nome_mes": nome_mes,
        "mes_anterior": mes_anterior,
        "ano_anterior": ano_anterior,
        "mes_proximo": mes_proximo,
        "ano_proximo": ano_proximo,
        "dados_motoristas": json.dumps(list(dados_motoristas)),
        "dados_dias_motoristas": json.dumps(list(dados_dias_motoristas)),
    })

@login_required(login_url='/login/')
def cadastrar_setor_externo(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        chefe_imediato = request.POST.get("chefe_imediato")
        cargo_chefe = request.POST.get("cargo_chefe")
        matricula_chefe = request.POST.get("matricula")
        portaria_chefe = request.POST.get("portaria_chefe")

        if nome:
            # Verifica se já existe setor com a mesma matrícula
            if Setor.objects.filter(matricula_chefe=matricula_chefe).exists():
                messages.error(request, f"Já existe um setor cadastrado com a matrícula {matricula_chefe}.")
            # Verifica se já existe setor com o mesmo nome
            elif Setor.objects.filter(nome__iexact=nome).exists():
                messages.error(request, f"Já existe um setor cadastrado com o nome '{nome}'.")
            else:
                setor = Setor.objects.create(
                    nome=nome,
                    chefe_imediato=chefe_imediato,
                    cargo_chefe=cargo_chefe,
                    matricula_chefe=matricula_chefe,
                    portaria_chefe=portaria_chefe,
                )
                messages.success(request, f"Setor '{setor.nome}' cadastrado com sucesso com chefe '{chefe_imediato}'.")
                return redirect("cadastrar_motorista_externo")

    setores = Setor.objects.all()
    return render(request, "agendamentos/cadastrar_setor_externo.html", {"setores": setores})

@login_required(login_url='/login/')
def cancelar_agendamento(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)

    # só pode cancelar se já estiver processado
    if agendamento.status != "processado":
        messages.error(request, "Só é possível cancelar agendamentos já processados.")
        return redirect("listar_agendamentos")

    # muda status para cancelado
    agendamento.status = "cancelado"
    agendamento.save()

    # se motorista for servidor interno, libera ele e passa para o próximo da fila
    if hasattr(agendamento, "processamento") and agendamento.processamento.motorista_servidor:
        processamento = agendamento.processamento

        # Se motorista for servidor interno
        motorista_cancelado = agendamento.processamento.motorista_servidor
        motorista_cancelado.ultima_vez_sorteado = datetime(1900, 1, 1)  # volta para o início da fila
        motorista_cancelado.save()

        # Remove vínculo do processamento
        processamento.motorista_servidor = None
        processamento.save()
        
        
        messages.info(request, f"O motorista {motorista_cancelado.nome} foi liberado e será o próximo da fila.")

    messages.success(request, "Agendamento cancelado com sucesso.")
    return redirect("listar_agendamentos")

@login_required(login_url='/login/')
def adicionar_memorando_agendamento(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)

    if request.method == "POST":
        numero = request.POST.get("n_memorando")
        servidor = getattr(request.user, "servidor", None)

        agendamento.n_memorando = numero
        if servidor:
            agendamento.memorando_servidor = servidor
            agendamento.memorando_nome = servidor.nome
            agendamento.memorando_matricula = servidor.matricula
            agendamento.memorando_setor = servidor.setor.nome if servidor.setor else ""
        if not request.user.servidor:
                messages.error(request, "Seu usuário não está vinculado a um servidor. Contate o administrador.")
                return redirect('home')
        agendamento.save()

        messages.success(request, "Memorando registrado com sucesso.")
        return redirect("listar_agendamentos")

    return render(request, "agendamentos/adicionar_memorando.html", {"agendamento": agendamento})


@login_required(login_url='/login/')
def gerar_pdf_solicitacao_veiculo(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)

    periodo_formatado = formatar_periodo(agendamento.data_ida, agendamento.data_retorno)
    # Renderiza HTML com os dados do agendamento
    html_string = render_to_string("pdf_solicitacao_veiculo.html", {
        "agendamento": agendamento,
        "periodo_formatado": periodo_formatado,
    })

    # Gera PDF em memória
    pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

    # Retorna como download
    response = HttpResponse(pdf_file, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="agendamento_{agendamento.id}.pdf"'
    return response

@login_required(login_url='/login/')
def calendario_motorista_pessoal(request):
    usuario = request.user
    if not hasattr(usuario, "servidor") or "Motorista" not in usuario.servidor.cargo:
        messages.error(request, "Você não tem permissão para acessar este calendário.")
        return redirect("listar_agendamentos")

    motorista = usuario.servidor
    ano = int(request.GET.get("ano", timezone.now().year))
    mes = int(request.GET.get("mes", timezone.now().month))
    # calcula a diferença de dias entre hoje e cada agendamento
    hoje = date.today()
    mais_proxima = None
    menor_diferenca = None

    cal = calendar.Calendar(firstweekday=6)
    semanas = cal.monthdayscalendar(ano, mes)

    agendamentos = ProcessamentoAgendamento.objects.filter(
        motorista_servidor=motorista,
        agendamento__data_ida__month=mes,
        agendamento__data_ida__year=ano,
        agendamento__status="processado"
    ).exclude(agendamento__status="cancelado").select_related("agendamento")

    # mapa de dias -> municípios
    colors = ["#f46236", "#2196f3", "#4caf50", "#ff9800", "#b031c7", "#00bcd4", "#AD8273", "#7fa0b1"]

    ocupados_map = {}
    viagens = []

    for idx, proc in enumerate(agendamentos):
        ag = proc.agendamento
        cor = colors[idx % len(colors)]  # pega cor da paleta ciclicamente
        periodo = formatar_periodo(ag.data_ida, ag.data_retorno)
        for dia in range(ag.data_ida.day, ag.data_retorno.day + 1):
            ocupados_map.setdefault(dia, []).append({"municipio": ag.municipio, "cor": cor})

        # só considera se a data de ida for hoje ou futura
        if ag.data_ida >= hoje:
            diferenca = (ag.data_ida - hoje).days
            if menor_diferenca is None or diferenca < menor_diferenca:
                menor_diferenca = diferenca
                mais_proxima = idx
        viagens.append({
            "municipio": ag.municipio,
            "periodo": periodo,
            "cor": cor,
            "data_ida": ag.data_ida,
        })
    # ordena pela data_ida (do menor para o maior)
    viagens = sorted(viagens, key=lambda x: x["data_ida"])
    # marca o agendamento mais próximo
    for viagem in viagens:
        if viagem["data_ida"] >= hoje:
            viagem["mais_proxima"] = True
            break  # só a primeira futura/atual

    # transforma semanas em estrutura com municípios + cor
    semanas_com_dados = []
    for semana in semanas:
        dias = []
        for dia in semana:
            if dia == 0:
                dias.append({"numero": 0, "municipios": []})
            else:
                dias.append({"numero": dia, "municipios": ocupados_map.get(dia, [])})
        semanas_com_dados.append(dias)

    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = mes + 1 if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1
    nome_mes = calendar.month_name[mes].capitalize()

    return render(request, "agendamentos/calendario_motorista_pessoal.html", {
        "motorista": motorista,
        "semanas": semanas_com_dados,
        "mes": mes,
        "ano": ano,
        "nome_mes": nome_mes,
        "mes_anterior": mes_anterior,
        "ano_anterior": ano_anterior,
        "mes_proximo": mes_proximo,
        "ano_proximo": ano_proximo,
        "viagens": viagens,
    })
