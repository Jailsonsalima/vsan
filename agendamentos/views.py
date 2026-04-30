from django.shortcuts import render, redirect

# Create your views here.

from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from .forms import AgendamentoForm, ProcessamentoAgendamentoForm, MotoristaExternoForm
from django.contrib import messages
from .models import Agendamento, AutorizacaoAgendamento, MotoristaExterno, ProcessamentoAgendamento
from usuarios.models import Usuario
from servidores.models import Servidor
from django.utils import timezone


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
            agendamento.save()

            # Envia e-mail ao solicitante
            send_mail(
                'Solicitação de Agendamento Recebida',
                f'Sua solicitação foi registrada. Aguarde confirmação.\n\n'
                f'Dados do agendamento:\n'
                f'Ida: {agendamento.data_ida.strftime("%d/%m/%Y")}\n'
                f'Retorno: {agendamento.data_retorno.strftime("%d/%m/%Y")}\n'
                f'Município: {agendamento.municipio}\n'
                f'Motivo: {agendamento.motivo}',
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


@login_required(login_url='/login/')
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


@login_required(login_url='/login/')
def processar_agendamento(request, agendamento_id):
    agendamento = Agendamento.objects.get(id=agendamento_id)

    # Verifica permissão
    autorizacao = AutorizacaoAgendamento.objects.filter(usuario=request.user, pode_processar=True).first()
    if not autorizacao and request.user.tipo_usuario != 'diretor':
        messages.error(request, "Você não tem permissão para processar agendamentos.")
        return redirect('listar_agendamentos')

    # Impede reprocessamento
    if agendamento.processado or ProcessamentoAgendamento.objects.filter(agendamento=agendamento).exists():
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

            # Recupera motorista sorteado da sessão
            if processamento.tipo == "Da Vigilância":
                # Seleciona o motorista com a data mais antiga (ou nula)
                motorista_sorteado = motoristas_servidores_disponiveis.order_by('ultima_vez_sorteado').first()
                if motorista_sorteado:
                    processamento.motorista_servidor = motorista_sorteado
                    motorista_sorteado.ultima_vez_sorteado = timezone.now()
                    motorista_sorteado.save()
                else:
                    # Nenhum motorista interno disponível
                    messages.error(request, "Não há motorista disponível da Vigilância. Selecione um motorista externo.")
                    return render(request, 'agendamentos/processar.html', {
                        'form': form,
                        'agendamento': agendamento,
                        'motorista_sorteado': None,
                        'aviso_motorista': "Não há motorista disponível da Vigilância. Selecione um motorista externo."
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
            agendamento.processado = True
            agendamento.save()

            # E-mail ao solicitante
            motorista_nome = None
            motorista_telefone = None
            if processamento.motorista_servidor:
                motorista_nome = processamento.motorista_servidor.nome
                motorista_telefone = getattr(processamento.motorista_servidor, "telefone", None)
            elif processamento.motorista_externo:
                motorista_nome = processamento.motorista_externo.nome_completo
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
        if motoristas_servidores_disponiveis.exists():
            motorista_sorteado = motoristas_servidores_disponiveis.order_by('ultima_vez_sorteado').first()
        else:
            aviso_motorista = "Não há motorista disponível da Vigilância. Selecione um motorista externo."

    return render(request, 'agendamentos/processar.html', {
        'form': form,
        'agendamento': agendamento,
        'motorista_sorteado': motorista_sorteado,
        'aviso_motorista': aviso_motorista,
    })

@login_required(login_url='/login/')
def listar_agendamentos(request):
    # Apenas usuários autorizados podem visualizar
    autorizacao = AutorizacaoAgendamento.objects.filter(usuario=request.user, pode_visualizar=True).first()
    if not autorizacao and request.user.tipo_usuario != 'diretor':
        messages.error(request, "Você não tem permissão para visualizar os agendamentos.")
        return render(request, "usuarios/dashboard.html")

    # Busca todos os agendamentos
    agendamentos = Agendamento.objects.all().order_by("-data_solicitacao").select_related("processamento")

    return render(request, "agendamentos/listar.html", {"agendamentos": agendamentos})

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
    if request.method == 'POST':
        form = MotoristaExternoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Motorista externo cadastrado com sucesso.")
            return redirect('listar_agendamentos')
    else:
        form = MotoristaExternoForm()

    return render(request, 'agendamentos/motorista_externo_form.html', {'form': form})

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
