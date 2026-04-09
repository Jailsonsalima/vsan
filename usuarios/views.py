from django.shortcuts import get_object_or_404, render, redirect
from setores.models import Setor
from .models import Usuario
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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

        if password1 != password2:
            messages.error(request, 'As senhas não coincidem.')
        else:
            setor = Setor.objects.get(id=setor_id)
            usuario = Usuario.objects.create_user(username=username, email=email, setor=setor, password=password1)
            usuario.save()
            return render(request, 'usuarios/sucesso.html')
    return render(request, 'usuarios/cadastrar_usuario.html', {'setores': setores})

def sucesso(request):
    return render(request, 'usuarios/sucesso.html')

@login_required
def dashboard(request):
    usuarios = Usuario.objects.filter(is_superuser=False)  # Exclui superusuários da lista
    setores = Setor.objects.all()
    return render(request, 'usuarios/dashboard.html', {'usuarios': usuarios, 'setores': setores})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # redireciona para a rota do dashboard
        else:
            messages.error(request, 'Credenciais inválidas.')
    return render(request, 'usuarios/login.html')


def logout_view(request):
    logout(request)
    return render(request, 'usuarios/home.html')


@login_required
def definir_tipo_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
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
