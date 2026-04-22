from django import forms
from .models import Agendamento, ProcessamentoAgendamento, MotoristaExterno
from servidores.models import Servidor

# Formulário de solicitação de agendamento
class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['data_ida', 'data_retorno', 'municipio', 'motivo']
        widgets = {
            'data_ida': forms.DateInput(attrs={'type': 'date', 'id': 'data_ida'}),
            'data_retorno': forms.DateInput(attrs={'type': 'date', 'id': 'data_retorno'}),
            'municipio': forms.TextInput(attrs={'id': 'municipio'}),
            'motivo': forms.Textarea(attrs={'rows': 3, 'id': 'motivo'}),
        }


# Formulário de processamento de agendamento
class ProcessamentoAgendamentoForm(forms.ModelForm):
    class Meta:
        model = ProcessamentoAgendamento
        fields = ['numero_processo', 'tipo', 'motorista_servidor', 'motorista_externo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Lista apenas motoristas internos (servidores com cargo "Motorista")
        self.fields['motorista_servidor'].queryset = Servidor.objects.filter(cargo__icontains="Motorista")

        # Lista todos motoristas externos cadastrados
        self.fields['motorista_externo'].queryset = MotoristaExterno.objects.all()

        # Ajusta widgets
        self.fields['numero_processo'].widget = forms.TextInput(attrs={'placeholder': 'Número do processo'})
        self.fields['tipo'].widget = forms.Select(choices=[('servidor', 'Servidor'), ('outros', 'Outros')])


class MotoristaExternoForm(forms.ModelForm):
    class Meta:
        model = MotoristaExterno
        fields = [
            "nome_completo", "cpf", "rg", "nascimento", "endereco", "vinculo",
            "matricula", "lotacao", "cargo", "funcao", "banco", "agencia",
            "conta_corrente", "disponivel"
        ]
        widgets = {
            "nascimento": forms.DateInput(attrs={"type": "date"}),
            "cpf": forms.TextInput(attrs={"type": "text", "placeholder": "Digite o CPF", "id": "cpf"}),
        }
