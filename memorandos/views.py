from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Memorando
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

def enviar_email_memorando(acao, memorando, usuario):
    assunto = f"Memorando {memorando.numero}/{memorando.ano} {acao}"
    mensagem = (
        f"O memorando foi {acao}.\n\n"
        f"Número: {memorando.numero}/{memorando.ano}\n"
        f"Servidor: {usuario}\n"
        f"Setor: {usuario.setor}\n"
        f"Data: {timezone.now().strftime('%d/%m/%Y %H:%M')}\n"
    )
    destinatario = [settings.EMAIL_HOST_USER, usuario.email]  # envia para admin + servidor
    send_mail(
        assunto,
        mensagem,
        settings.DEFAULT_FROM_EMAIL,
        destinatario,
        fail_silently=False,
    )

def ano_simulado():
    return 2029

@login_required
def gerenciar_memorando(request):
    data_uso=timezone.now()
    ano_atual = data_uso.year
    existe_inicial = Memorando.objects.exists()
    numero_gerado = None
    
    # Área 0: Configurar número inicial (somente diretor)
    if 'numero_inicial' in request.POST and request.user.tipo_usuario == "diretor":
        numero_inicial = request.POST.get("numero_inicial")
        if numero_inicial:
            if Memorando.objects.exists():
                messages.error(request, "Já existe um número cadastrado. Não é possível definir outro número inicial.")
            else:
                memorando = Memorando(
                    numero=numero_inicial,
                    ano=ano_atual,
                    servidor=request.user,
                    setor=request.user.setor if request.user.setor else None,
                    data_uso=data_uso
                )
                memorando.save()
                messages.success(request, f"Primeiro número {numero_inicial}/{ano_atual} configurado com sucesso!")
                return redirect('gerenciar_memorando')

    # Área 1: Gerar número
    if 'gerar' in request.POST:
        existe_ano_atual = Memorando.objects.filter(ano=ano_atual).exists()
        if not existe_inicial:
            messages.error(request, "O diretor deve definir o primeiro número antes de gerar memorandos.")
        else:
        # Verificação de bloqueio em segundos
            ultimo = Memorando.objects.filter(ano=ano_atual).order_by('-data_uso').first()
            if ultimo and ultimo.servidor == request.user:
                tempo_passado = data_uso - ultimo.data_uso
                segundos = 60
                if tempo_passado < timedelta(seconds=segundos):
                    segundos_restantes = segundos - int(tempo_passado.total_seconds())
                    messages.error(
                        request,
                        f"Você gerou o memorando {ultimo.numero}/{ultimo.ano} há {int(tempo_passado.total_seconds())} segundos. \n"
                        f"Aguarde {segundos_restantes} segundos para gerar novamente."
                    )
                    return redirect('gerenciar_memorando')
        if not existe_ano_atual:
            proximo_num = 1
            numero_formatado = f"{proximo_num:04d}/{ano_atual}"
            memorando = Memorando.objects.create(
                numero=f"{proximo_num:04d}",
                ano=ano_atual,
                servidor=request.user,
                setor=request.user.setor if request.user.setor else None,
                data_uso=data_uso
            )
            numero_gerado = numero_formatado
            messages.success(request, f"Memorando {numero_formatado} iniciado automaticamente para o novo ano!")
            enviar_email_memorando("gerado", memorando, request.user)
        else:
            devolvido = Memorando.objects.filter(ano=ano_atual, devolvido=True).order_by('id').first()
            if devolvido:
                devolvido.devolvido = False
                devolvido.servidor = request.user
                devolvido.setor = request.user.setor if request.user.setor else None
                devolvido.data_uso = data_uso
                devolvido.save()
                numero_formatado = f"{devolvido.numero}/{ano_atual}"
                numero_gerado = numero_formatado
                messages.success(request, f"Memorando {numero_formatado} reutilizado com sucesso!")
                enviar_email_memorando("reutilizado", devolvido, request.user)
            else:
                ultimo = Memorando.objects.filter(ano=ano_atual).order_by('-id').first()
                proximo_num = int(ultimo.numero) + 1 if ultimo else 1
                numero_formatado = f"{proximo_num:04d}/{ano_atual}"
                memorando = Memorando.objects.create(
                    numero=f"{proximo_num:04d}",
                    ano=ano_atual,
                    servidor=request.user,
                    setor=request.user.setor if request.user.setor else None,
                    data_uso = data_uso
                )
                numero_gerado = numero_formatado
                messages.success(request, f"Memorando {numero_formatado} gerado com sucesso!")
                enviar_email_memorando("gerado", memorando, request.user)

    # Área 2: Devolver número
    if 'devolver' in request.POST:
        numero_devolvido = request.POST.get('numero_devolvido')
        memorando = Memorando.objects.filter(numero=numero_devolvido, ano=ano_atual).first()
        if memorando:
            if memorando.servidor == request.user:
                memorando.devolvido = True
                memorando.save()
                numero_gerado = f"{numero_devolvido}/{ano_atual}"
                messages.success(request, f"Memorando {numero_devolvido}/{ano_atual} devolvido com sucesso!")
                enviar_email_memorando("devolvido", memorando, request.user)
            else:
                messages.error(request, "Você não pode devolver um número que não foi gerado por você.")
        else:
            messages.error(request, "Número não encontrado.")

    # Histórico conforme perfil
    if request.user.tipo_usuario == "diretor":
        memorandos = Memorando.objects.all().order_by('-data_uso')
    elif request.user.tipo_usuario == "coordenador":
        memorandos = Memorando.objects.filter(setor=request.user.setor).order_by('-data_uso')
    else:
        memorandos = Memorando.objects.filter(servidor=request.user).order_by('-data_uso')

    return render(request, 'memorandos/gerenciar_memorando.html', {
        'memorandos': memorandos,
        'existe_inicial': existe_inicial,
        'numero_gerado': numero_gerado
    })
