from django.shortcuts import render, redirect
from .models import Servidor
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.templatetags.static import static

def cadastro_servidor(request):
    if request.method == "POST":
        servidor = Servidor.objects.create(
            nome=request.POST.get("nome"),
            endereco=request.POST.get("endereco"),
            vinculo=request.POST.get("vinculo"),
            matricula=request.POST.get("matricula"),
            lotacao=request.POST.get("lotacao"),
            cargo=request.POST.get("cargo"),
            funcao=request.POST.get("funcao"),
            periodo_viagem=request.POST.get("periodo_viagem"),
            dias_diarias=request.POST.get("dias_diarias"),
            pernoite=request.POST.get("pernoite"),
            cpf=request.POST.get("cpf"),
            rg=request.POST.get("rg"),
            nascimento=request.POST.get("nascimento") or None,
            transporte=request.POST.get("transporte"),
            banco=request.POST.get("banco"),
            agencia=request.POST.get("agencia"),
            conta=request.POST.get("conta"),
            objetivo=request.POST.get("objetivo"),
            data=request.POST.get("data") or None,
            chefia=request.POST.get("chefia"),
        )
        return redirect("lista_servidores")  # rota para listar servidores
        
    # Se for GET, mostra o formulário
    return render(request, "servidores/cadastro_servidor.html")


def gerar_pdf_servidores(request):
    if request.method == "POST":
        ids = request.POST.getlist("servidores")  # lista de IDs selecionados
        servidores = Servidor.objects.filter(id__in=ids)

        # renderiza o HTML e injeta STATIC_URL
        html_string = render_to_string(
            "servidores/pdf_modelo.html",
            {"servidores": servidores, "STATIC_URL": static("")}
        )

        # base_url é essencial para que o WeasyPrint consiga resolver imagens e CSS
        pdf_file = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response['Content-Disposition'] = 'inline; filename="servidores.pdf"'
        return response

    servidores = Servidor.objects.all()
    return render(request, "servidores/selecionar_servidores.html", {"servidores": servidores})

def lista_servidores(request):
    servidores = Servidor.objects.all()
    return render(request, "servidores/lista_servidores.html", {"servidores": servidores})

