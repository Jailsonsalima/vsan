// script.js

document.addEventListener("DOMContentLoaded", function () {
    
    
    // --- Matrícula ---
    const matriculaInput = document.getElementById("matricula");
    if (matriculaInput) {
        matriculaInput.addEventListener("input", function (e) {
            let valor = e.target.value.replace(/\D/g, ""); // só números
            if (valor.length > 1) {
                valor = valor.slice(0, -1) + "/" + valor.slice(-1);
            }
            e.target.value = valor;
        });
    }

    // --- CPF ---
    const cpfInput = document.getElementById("cpf");
    if (cpfInput) {
        cpfInput.addEventListener("input", function (e) {
            let valor = e.target.value.replace(/\D/g, ""); // só números
            if (valor.length > 11) valor = valor.slice(0, 11);

            valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
            valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
            valor = valor.replace(/(\d{3})(\d{1,2})$/, "$1-$2");

            e.target.value = valor;
        });
    }

    // --- Validação idade ---
    function validarIdade() {
        const nascimentoInput = document.getElementById("nascimento");
        if (!nascimentoInput) return;

        const valor = nascimentoInput.value;
        if (!valor) return;

        const nascimento = new Date(valor);
        const hoje = new Date();

        let idade = hoje.getFullYear() - nascimento.getFullYear();
        const m = hoje.getMonth() - nascimento.getMonth();
        if (m < 0 || (m === 0 && hoje.getDate() < nascimento.getDate())) {
            idade--;
        }

        let aviso = document.getElementById("aviso-idade");
        if (aviso) aviso.remove();

        if (idade < 18) {
            aviso = document.createElement("div");
            aviso.id = "aviso-idade";
            aviso.style.color = "red";
            aviso.style.marginTop = "5px";
            aviso.textContent = "⚠ O servidor deve ter pelo menos 18 anos.";
            nascimentoInput.parentNode.appendChild(aviso);
        }
    }

    // --- Validação data de partida ---
    function validarPartida() {
        const data_idaInput = document.getElementById("data_ida");
        if (!data_idaInput) return;

        const valor = data_idaInput.value;
        if (!valor) return;

        const data_ida = new Date(valor);
        const hoje = new Date();

        data_ida.setHours(0, 0, 0, 0);
        hoje.setHours(0, 0, 0, 0);

        const diffTime = data_ida.getTime() - hoje.getTime()+1;
        const diasPartida = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        let aviso = document.getElementById("aviso-data_ida");
        if (aviso) aviso.remove();

        if (diasPartida < 0) {
            aviso = document.createElement("div");
            aviso.id = "aviso-data_ida";
            aviso.style.color = "red";
            aviso.style.marginTop = "5px";
            aviso.textContent = "⚠ A data de partida deve ser igual ou posterior ao dia atual.";
            data_idaInput.parentNode.appendChild(aviso);
        }
    }

    // --- Validação data de retorno ---
    function validarRetorno() {
        const data_idaInput = document.getElementById("data_ida");
        const data_retornoInput = document.getElementById("data_retorno");
        if (!data_retornoInput) return;

        const valorRetorno = data_retornoInput.value;
        if (!valorRetorno) return;

        const data_retorno = new Date(valorRetorno);
        const hoje = new Date();
        data_retorno.setHours(0, 0, 0, 0);
        hoje.setHours(0, 0, 0, 0);

        let aviso = document.getElementById("aviso-data_retorno");
        if (aviso) aviso.remove();

        if (data_retorno < hoje) {
            aviso = document.createElement("div");
            aviso.id = "aviso-data_retorno";
            aviso.style.color = "red";
            aviso.style.marginTop = "5px";
            aviso.textContent = "⚠ A data de retorno deve ser igual ou posterior ao dia atual.";
            data_retornoInput.parentNode.appendChild(aviso);
            return;
        }

        if (data_idaInput.value) {
            const data_ida = new Date(data_idaInput.value);
            data_ida.setHours(0, 0, 0, 0);

            const diffTime = data_retorno.getTime() - data_ida.getTime();
            const diffDias = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (diffDias < 0) {
                aviso = document.createElement("div");
                aviso.id = "aviso-data_retorno";
                aviso.style.color = "red";
                aviso.style.marginTop = "5px";
                aviso.textContent = "⚠ A data de retorno não pode ser anterior a data de ida.";
                data_retornoInput.parentNode.appendChild(aviso);
            }
        }
    }

    // --- Cálculo de dias/diárias ---
    function calcularDias() {
        const dataIda = document.getElementById("data_ida").value;
        const dataRetorno = document.getElementById("data_retorno").value;
        const pernoiteSim = document.getElementById("pernoite_sim").checked;
        const pernoiteNao = document.getElementById("pernoite_nao").checked;
        const campoDias = document.getElementById("dias_diarias");

        if (!dataIda || !dataRetorno) {
            campoDias.value = "";
            return;
        }

        const ida = new Date(dataIda);
        const retorno = new Date(dataRetorno);

        const diffTime = retorno - ida;
        const diasViagem = diffTime / (1000 * 60 * 60 * 24) + 1;

        let resultado = "";
        if (pernoiteSim) {
            resultado = `${diasViagem} / ${(diasViagem - 0.5).toString().replace(".", ",")}`;
        } else if (pernoiteNao) {
            resultado = `${diasViagem} / ${(diasViagem / 2).toString().replace(".", ",")}`;
        }

        campoDias.value = resultado;
    }

    // --- Eventos ---
    const nascimentoInput = document.getElementById("nascimento");
    if (nascimentoInput) nascimentoInput.addEventListener("input", validarIdade);

    const data_idaInput = document.getElementById("data_ida");
    if (data_idaInput) {
        data_idaInput.addEventListener("input", validarPartida);
        data_idaInput.addEventListener("change", calcularDias);
    }

    const data_retornoInput = document.getElementById("data_retorno");
    if (data_retornoInput) {
        data_retornoInput.addEventListener("input", validarRetorno);
        data_retornoInput.addEventListener("change", calcularDias);
    }

    const pernoiteSim = document.getElementById("pernoite_sim");
    const pernoiteNao = document.getElementById("pernoite_nao");
    if (pernoiteSim) pernoiteSim.addEventListener("change", calcularDias);
    if (pernoiteNao) pernoiteNao.addEventListener("change", calcularDias);

    // --- Botão habilitado apenas se houver servidores selecionados ---
    const checkboxes = document.querySelectorAll('input[name="servidores"]');
    const btnProximo = document.getElementById('btn-proximo');

    function atualizarBotao() {
        const algumSelecionado = Array.from(checkboxes).some(c => c.checked);
        btnProximo.disabled = !algumSelecionado;

        if (algumSelecionado) {
            btnProximo.classList.remove('btn-disabled');
            btnProximo.classList.add('btn-secondary');
        } else {
            btnProximo.classList.remove('btn-secondary');
            btnProximo.classList.add('btn-disabled');
        }
    }
    checkboxes.forEach(cb => cb.addEventListener('change', atualizarBotao));

// --- Filtro de pesquisa de servidores ---
document.getElementById("filtro-servidores").addEventListener("keyup", function() {
    const filtro = this.value.toLowerCase();
    const servidores = document.querySelectorAll("#lista-servidores .servidor-item");

    servidores.forEach(function(item) {
        const texto = item.textContent.toLowerCase();
        item.style.display = texto.includes(filtro) ? "" : "none";
    });
});

// --- Lista de servidores selecionados ---
const listaSelecionados = document.getElementById('servidores-selecionados');

function atualizarLista() {
    listaSelecionados.innerHTML = "";
    checkboxes.forEach(cb => {
        if (cb.checked) {
            const li = document.createElement("li");
            li.textContent = cb.getAttribute("data-nome");
            listaSelecionados.appendChild(li);
        }
    });
}
checkboxes.forEach(cb => cb.addEventListener('change', atualizarLista));

 
});
