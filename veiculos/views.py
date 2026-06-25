from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Veiculo

@login_required(login_url='/login/')
def listar_veiculos(request):
    veiculos = Veiculo.objects.all().order_by("modelo")
    return render(request, "veiculos/listar_veiculos.html", {"veiculos": veiculos})

@login_required(login_url='/login/')
def cadastrar_veiculo(request):
    if request.method == "POST":
        modelo = request.POST.get("modelo")
        placa = request.POST.get("placa")

        if not modelo or not placa:
            messages.error(request, "Preencha todos os campos.")
            return redirect("cadastrar_veiculo")

        if Veiculo.objects.filter(placa=placa).exists():
            messages.error(request, "Já existe um veículo com essa placa.")
            return redirect("cadastrar_veiculo")

        Veiculo.objects.create(modelo=modelo, placa=placa)
        messages.success(request, "Veículo cadastrado com sucesso!")
        return redirect("listar_veiculos")

    return render(request, "veiculos/cadastrar_veiculo.html")

@login_required(login_url='/login/')
def editar_veiculo(request, veiculo_id):
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)
    if request.method == "POST":
        veiculo.modelo = request.POST.get("modelo")
        veiculo.placa = request.POST.get("placa")
        veiculo.save()
        messages.success(request, "Veículo atualizado com sucesso!")
        return redirect("listar_veiculos")
    return render(request, "veiculos/editar_veiculo.html", {"veiculo": veiculo})

@login_required(login_url='/login/')
def excluir_veiculo(request, veiculo_id):
    veiculo = get_object_or_404(Veiculo, id=veiculo_id)
    veiculo.delete()
    messages.success(request, "Veículo excluído com sucesso!")
    return redirect("listar_veiculos")
