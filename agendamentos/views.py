from django.shortcuts import render, redirect

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .forms import AgendamentoForm, ProcessamentoAgendamentoForm, MotoristaExternoForm
from django.contrib import messages
from .models import Agendamento, AutorizacaoAgendamento, MotoristaExterno, ProcessamentoAgendamento
from usuarios.models import Usuario
from servidores.models import Servidor


@login_required
def solicitar_agendamento(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.solicitante = request.user
            agendamento.servidor = request.user.servidor
            agendamento.save()

            # Envia e-mail ao solicitante
            send_mail(
                'Solicitação de Agendamento Recebida',
                f'Sua solicitação foi registrada. Aguarde confirmação.\nDados: {agendamento}',
                'sistema@vsan.com',
                [request.user.email],
            )

            # Envia e-mail aos usuários autorizados (diretor define quem recebe)
            autorizados = AutorizacaoAgendamento.objects.filter(pode_visualizar=True)
            for autorizacao in autorizados:
                send_mail(
                    'Novo Pedido de Agendamento',
                    f'Um novo agendamento foi solicitado.\nDados: {agendamento}',
                    'sistema@vsan.com',
                    [autorizacao.usuario.email],
                )
            return redirect('dashboard')
    else:
        form = AgendamentoForm()
    return render(request, 'agendamentos/solicitar.html', {'form': form})


@login_required
def gerenciar_autorizacoes(request):
    if request.user.tipo_usuario != 'diretor':
        messages.error(request, "Apenas diretores podem gerenciar autorizações.")
        return redirect('dashboard')

    usuarios = Usuario.objects.filter(is_superuser=False).exclude(id=request.user.id)

    # garante que cada usuário tenha um objeto de autorização
    for usuario in usuarios:
        autorizacao, _ = AutorizacaoAgendamento.objects.get_or_create(usuario=usuario)
        usuario.autorizacao = autorizacao
        
    motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista")
    motoristas_externos = MotoristaExterno.objects.all()

    if request.method == 'POST':
        for usuario in usuarios:
            visualizar = request.POST.get(f"visualizar_{usuario.id}") == "on"
            processar = request.POST.get(f"processar_{usuario.id}") == "on"
            autorizacao, _ = AutorizacaoAgendamento.objects.get_or_create(usuario=usuario)
            usuario.autorizacao.pode_visualizar = visualizar
            usuario.autorizacao.pode_processar = processar
            usuario.autorizacao.save()
        messages.success(request, "Autorizações de usuários atualizadas com sucesso.")
        return redirect('gerenciar_autorizacoes')

    return render(request, 'agendamentos/gerenciar_autorizacoes.html', {
        'usuarios': usuarios,
        'motoristas_servidores': motoristas_servidores,
        'motoristas_externos': motoristas_externos  # para exibir também na mesma página
    })


@login_required
def processar_agendamento(request, agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)

    # Impede reprocessamento
    if agendamento.processado or ProcessamentoAgendamento.objects.filter(agendamento=agendamento).exists():
        messages.error(request, "Este agendamento já foi processado e não pode ser alterado novamente.")
        return redirect('listar_agendamentos')
    
    motoristas_servidores = Servidor.objects.filter(cargo__icontains="Motorista")
    motoristas_externos = MotoristaExterno.objects.all()

    motoristas = []

    def verificar_disponibilidade(motorista, tipo="servidor"):
        filtro = {}
        if tipo == "servidor":
            filtro["motorista_servidor"] = motorista
        else:
            filtro["motorista_externo"] = motorista

        processamento_ativo = ProcessamentoAgendamento.objects.filter(
            **filtro,
            agendamento__data_ida__lte=agendamento.data_retorno,
            agendamento__data_retorno__gte=agendamento.data_ida
        ).first()

        status = "disponivel"
        periodo = None

        if processamento_ativo:
            status = "em_viagem"
            periodo = f"{processamento_ativo.agendamento.data_ida} - {processamento_ativo.agendamento.data_retorno}"
        elif not motorista.disponivel:
            status = "indisponivel"

        return {
            "nome": getattr(motorista, "nome", getattr(motorista, "nome_completo", "")),
            "status": status,
            "periodo": periodo,
            "tipo": tipo,
        }

    # monta lista de motoristas para exibição
    for m in motoristas_servidores:
        motoristas.append(verificar_disponibilidade(m, "servidor"))
    for m in motoristas_externos:
        motoristas.append(verificar_disponibilidade(m, "externo"))

    # filtra motoristas disponíveis para os selects
    # filtra motoristas disponíveis para os selects
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

    if request.method == 'POST':
        form = ProcessamentoAgendamentoForm(request.POST)
        if form.is_valid():
            processamento = form.save(commit=False)
            processamento.agendamento = agendamento
            processamento.save()
            agendamento.processado = True
            agendamento.save()

            # envia e-mail ao solicitante
            send_mail(
                'Agendamento Processado',
                f'Sua solicitação foi respondida.\n'
                f'Número do processo: {processamento.numero_processo}\n'
                f'Dados do agendamento:\n'
                f'Ida: {agendamento.data_ida}\n'
                f'Retorno: {agendamento.data_retorno}\n'
                f'Município: {agendamento.municipio}\n'
                f'Motivo: {agendamento.motivo}',
                'sistema@vsan.com',
                [agendamento.solicitante.email],
            )

            messages.success(request, "Agendamento processado com sucesso.")
            return redirect('listar_agendamentos')
    else:
        form = ProcessamentoAgendamentoForm()
        form.fields["motorista_servidor"].queryset = motoristas_servidores_disponiveis
        form.fields["motorista_externo"].queryset = motoristas_externos_disponiveis

    return render(request, 'agendamentos/processar.html', {
        'form': form,
        'agendamento': agendamento,
        'motoristas': motoristas,
    })

@login_required
def listar_agendamentos(request):
    # Apenas usuários autorizados podem visualizar
    autorizacao = AutorizacaoAgendamento.objects.filter(usuario=request.user, pode_visualizar=True).first()
    if not autorizacao and request.user.tipo_usuario != 'diretor':
        messages.error(request, "Você não tem permissão para visualizar os agendamentos.")
        return render(request, "usuarios/dashboard.html")

    # Busca todos os agendamentos
    agendamentos = Agendamento.objects.all().order_by("-data_solicitacao")

    return render(request, "agendamentos/listar.html", {"agendamentos": agendamentos})

@login_required
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

@login_required
def cadastrar_motorista_externo(request):
    if request.user.tipo_usuario != 'diretor':
        messages.error(request, "Apenas diretores podem cadastrar motoristas externos.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = MotoristaExternoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Motorista externo cadastrado com sucesso.")
            return redirect('gerenciar_motoristas')
    else:
        form = MotoristaExternoForm()

    return render(request, 'agendamentos/motorista_externo_form.html', {'form': form})
