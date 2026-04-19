"""
URL configuration for vsan project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from usuarios import views
from setores import views as setor_views
from servidores import views as servidor_views
from atividades import views as atividades_views

from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('cadastrar-usuario/', views.cadastrar_usuario, name='cadastrar_usuario'),
    path('cadastrar-setor/', setor_views.cadastrar_setor, name='cadastrar_setor'),
    path('setores/excluir/<int:setor_id>/', setor_views.excluir_setor, name='excluir_setor'),
    path('setores/', setor_views.listar_setores, name='listar_setores'),
    path('sucesso/', views.sucesso, name='sucesso'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('definir-tipo-usuario/<int:usuario_id>/', views.definir_tipo_usuario, name='definir_tipo_usuario'),
    path("cadastro_servidor/", servidor_views.cadastro_servidor, name="cadastro_servidor"),
    path("servidores/", servidor_views.lista_servidores, name="lista_servidores"),
    path('cadastro-atividade/', atividades_views.cadastrar_atividade, name="cadastrar_atividade"),
    path("atividade/<int:atividade_id>/pdfs/", atividades_views.gerar_zip_pdfs, name="gerar_zip_pdfs"),
    path("setores/editar/<int:setor_id>/", setor_views.editar_setor, name="editar_setor"),
    path("cadastro-servidor-publico/", servidor_views.cadastro_servidor_publico, name="cadastro_servidor_publico"),
    path("atividade/editar/<int:atividade_id>/", atividades_views.editar_atividade, name="editar_atividade"),

    # Solicitar redefinição
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    # Confirmação de envio de e-mail
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # Link recebido por e-mail
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # Finalização da redefinição
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
