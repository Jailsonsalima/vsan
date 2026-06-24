from django.shortcuts import render, redirect, get_object_or_404
from .models import Servidor, HistoricoSituacao
from setores.models import Setor
from django.contrib.auth.decorators import login_required
from datetime import date, datetime
from django.contrib import messages
from django.core.paginator import Paginator

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML

@login_required(login_url='/login/')
def cadastro_servidor(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        setor_id = request.POST.get("setor")
        setor = Setor.objects.get(id=setor_id) if setor_id else None
        nascimento_str = request.POST.get("nascimento")
        nascimento = None
        chefe_id = request.POST.get("chefe_imediato")
        chefe = Setor.objects.get(id=chefe_id) if chefe_id else None
        if nascimento_str:
            try:
                nascimento = datetime.strptime(nascimento_str, "%Y-%m-%d").date()
                # Calcula idade
                hoje = date.today()
                idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
                if idade < 18:
                    messages.error(request, "O servidor deve ter pelo menos 18 anos.")
                    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
        admissao_str = request.POST.get("admissao") or None
        admissao = None

        if admissao_str:
            try:
                # Supondo que o campo venha no formato "YYYY-MM-DD"
                admissao = datetime.strptime(admissao_str, "%Y-%m-%d").date()
            except ValueError:
                # Caso o formato seja inválido, você pode tratar aqui
                admissao = None
            
        servidor = Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.user.matricula,  # usa matrícula do usuário
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            setor=setor,  # vínculo com setor
            chefe_imediato=chefe,  # vínculo com chefe imediato

            admissao=request.POST.get("admissao") or None,
            horario_trabalho=request.POST.get("horario_trabalho"),
            orgao_origem=request.POST.get("orgao_origem"),
            telefone = request.POST.get("telefone"),
        )
        # Vincula o servidor ao usuário logado
        request.user.servidor = servidor
        request.user.save()
        messages.success(request, "Servidor cadastrado com sucesso! ")
        return redirect("dashboard")  # rota para segunda etapa de cadastro
    
    # Se for GET, mostra o formulário
    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})

def lista_servidores(request):
    servidores = Servidor.objects.all()
    return render(request, "servidores/lista_servidores.html", {"servidores": servidores})


def cadastro_servidor_publico(request):
    setores = Setor.objects.all()
    if request.method == "POST":
        setor_id = request.POST.get("setor")
        setor = Setor.objects.get(id=setor_id) if setor_id else None
        nascimento_str = request.POST.get("nascimento")
        nascimento = None
        if nascimento_str:
            try:
                nascimento = datetime.strptime(nascimento_str, "%Y-%m-%d").date()
                # Calcula idade
                hoje = date.today()
                idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
                if idade < 18:
                    messages.error(request, "O servidor deve ter pelo menos 18 anos.")
                    return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return render(request, "servidores/cadastro_servidor.html", {"setores": setores})
        chefe_id = request.POST.get("chefe_imediato")
        chefe = Setor.objects.get(id=chefe_id) if chefe_id else None
        admissao_str = request.POST.get("admissao") or None
        admissao = None

        if admissao_str:
            try:
                # Supondo que o campo venha no formato "YYYY-MM-DD"
                admissao = datetime.strptime(admissao_str, "%Y-%m-%d").date()
            except ValueError:
                # Caso o formato seja inválido, você pode tratar aqui
                admissao = None
        Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.POST.get("matricula"),  # matrícula obrigatória
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=nascimento,
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            setor=setor,  # vínculo com setor
            chefe_imediato=chefe,  # vínculo com chefe imediato

            admissao=admissao,
            horario_trabalho=request.POST.get("horario_trabalho"),
            orgao_origem=request.POST.get("orgao_origem"),
            telefone = request.POST.get("telefone"),
        )
        messages.success(request, "Servidor público cadastrado com sucesso! ")
        return redirect("sucesso")
    

    return render(request, "servidores/cadastro_servidor_publico.html", {"setores": setores})


@login_required(login_url='/login/')
def gerenciar_servidores(request):
    servidores = Servidor.objects.all().order_by("nome")

    # Paginação
    paginator = Paginator(servidores, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    if request.method == "POST":
        servidor_id = request.POST.get("servidor_id")
        situacao = request.POST.get("situacao")
        descricao = request.POST.get("descricao")

        servidor = Servidor.objects.get(id=servidor_id)

        # mês/ano automático do sistema
        hoje = datetime.today()
        HistoricoSituacao.objects.create(
            servidor=servidor,
            situacao=situacao,
            descricao=descricao,
            mes=hoje.month,
            ano=hoje.year
        )

        messages.success(request, f"Situação funcional de {servidor.nome} atualizada.")
        return redirect("gerenciar_servidores")

    return render(request, "servidores/gerenciar_servidores.html", {
        "page_obj": page_obj
    })


@login_required(login_url='/login/')
def historico_servidor(request, servidor_id):
    servidor = get_object_or_404(Servidor, id=servidor_id)
    historico = servidor.historico_situacoes.order_by("-ano", "-mes")  # mais recente primeiro

    return render(request, "servidores/historico_servidor.html", {
        "servidor": servidor,
        "historico": historico
    })


def gerar_boletim_pdf(request):
    registros = HistoricoSituacao.objects.all()
    context = {
        'registros': registros,
        'mes': 'Abril',
        'ano': '2026'
    }
    html_string = render_to_string('pdf_boletim_frequencia.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="boletim_frequencia.pdf"'
    return response


def gerar_mapa_pdf(request):
    servidores = Servidor.objects.all()
    #chefe_id = atividades.filter(municipio__icontains=municipio)
    #chefe = Setor.objects.get(id=chefe_id).filter(chefe_imediato__icontains="Diretor ")
    context = {
        'servidores': servidores,
        'mes': 'Abril',
        'ano': '2026',
        'data_atual': datetime.date.today()
    }
    html_string = render_to_string('pdf_mapa_frequencia.html', context)
    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="mapa_frequencia.pdf"'
    return response
