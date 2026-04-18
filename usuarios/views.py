from django.shortcuts import get_object_or_404, render, redirect
from setores.models import Setor
from .models import Usuario
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from atividades.models import Atividade
from servidores.models import Servidor

# Create your views here.
def home(request):
    return render(request, 'usuarios/home.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def cadastrar_usuario(request):
    setores = Setor.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        setor_id = request.POST.get('setor')
        password1 = request.POST.get('password')
        password2 = request.POST.get('password2')
        matricula = request.POST.get('matricula')

        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        else:
            setor = Setor.objects.get(id=setor_id)
            usuario = Usuario.objects.create_user(username=username, email=email, setor=setor, password=password1, matricula=matricula)
            # Se já existir servidor com essa matrícula, vincula e deixa inativo
            servidor_existente = Servidor.objects.filter(matricula=matricula).first()
            if servidor_existente:
                usuario.servidor = servidor_existente
                usuario.is_active = False  # conta fica inativa até ser ativada pelo diretor
                usuario.save()
            else:
                # Se não existir servidor, apenas salva o usuário sem vínculo
                usuario.save()
            return render(request, 'usuarios/sucesso.html')
    return render(request, 'usuarios/cadastrar_usuario.html', {'setores': setores})

def sucesso(request):
    return render(request, 'usuarios/sucesso.html')

from atividades.models import Atividade

@login_required
def dashboard(request):
    # Superuser sempre acessa
    if request.user.is_superuser:
        pass
    else:
        if not request.user.servidor:
            return redirect("cadastro_servidor")
    setores = Setor.objects.all()

    # Se o diretor clicar no botão "Ver todos", pegamos todos os usuários
    if request.GET.get("mostrar") == "todos":
        usuarios = Usuario.objects.filter(is_superuser=False)  # Exclui superusuários da lista
    else:
        # Por padrão, mostra apenas os inativos
        usuarios = Usuario.objects.filter(is_superuser=False, is_active=False)

    # Adiciona atividades ao contexto
    atividades = Atividade.objects.all().order_by("-data_criacao")

    return render(
        request,
        "usuarios/dashboard.html",
        {
            "usuarios": usuarios,
            "setores": setores,
            "atividades": atividades,
        },
    )

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            # Se for superuser, vai direto para o dashboard
            if user.is_superuser:
                return redirect('dashboard')

            # Se não for superuser, verifica vínculo com servidor
            #if hasattr(user, "servidor") and user.servidor is not None:
            # Se não for superuser, verifica vínculo com servidor
            if user.servidor:
                return redirect('dashboard')
            else:
                return redirect('cadastro_servidor')
        else:
            messages.error(request, 'Credenciais inválidas.')
    return render(request, 'usuarios/login.html')


def logout_view(request):
    logout(request)
    return render(request, 'usuarios/home.html')


@login_required
def definir_tipo_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    # Impede que o usuário altere a própria conta
    if usuario == request.user:
        messages.error(request, "Você não pode alterar o status da própria conta.")
        return redirect('dashboard')
    if request.method == 'POST':
        tipo_usuario = request.POST.get('tipo_usuario')
        setor_id = request.POST.get('setor')
        if tipo_usuario == "inativo":
            usuario.tipo_usuario = None
            usuario.is_active = False
        else:
            usuario.tipo_usuario = tipo_usuario
            usuario.is_active = True
        if setor_id:
            usuario.setor = Setor.objects.get(id=setor_id)

        usuario.save()  # ativa automaticamente se tiver tipo definido
        messages.success(request, f"Usuário {usuario.username} atualizado com sucesso.")
    return redirect('dashboard')
