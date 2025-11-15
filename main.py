from flask import Flask, render_template, request, jsonify
import requests
import hashlib
from datetime import datetime
import os
import re # Importa a biblioteca de RegEx

# Configura a aplicação Flask
app = Flask(__name__, template_folder='templates')

# --- CONFIGURAÇÃO ---
# !! COLE A SUA URL DO FIREBASE AQUI !!
FIREBASE_URL = "https://sistema-salao-59ac8-default-rtdb.firebaseio.com"

# --- FUNÇÕES AUXILIARES DO BACKEND ---
def hash_senha(senha):
    """Encripta a senha."""
    return hashlib.sha256(senha.encode('utf-8')).hexdigest()

def get_db_url(endpoint):
    """Gera a URL completa para a tabela (endpoint) no Firebase."""
    base = FIREBASE_URL.rstrip('/')
    if not endpoint.startswith('/'):
        endpoint = '/' + endpoint
    return f"{base}{endpoint}.json"

# --- ROTA 1: CARREGAR A PÁGINA (O FRONTEND) ---
@app.route('/')
def index():
    """Esta função carrega o seu ficheiro index.html quando alguém acede ao site."""
    return render_template('index.html')

# --- ROTA 2: API PARA LOGIN ---
@app.route('/api/login', methods=['POST'])
def api_login():
    """Esta é a função que o JavaScript chama quando o botão 'Entrar' é clicado."""
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    
    try:
        response = requests.get(get_db_url('contas'))
        contas = response.json() or {}
        senha_hash = hash_senha(senha)
        
        for uid, conta in contas.items():
            if conta.get('email') == email and conta.get('senha_hash') == senha_hash:
                conta['id'] = uid # Adiciona o ID único aos dados do utilizador
                return jsonify({"success": True, "user": conta})
        
        return jsonify({"success": False, "message": "E-mail ou senha incorretos."})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro no servidor: {e}"})

# --- ROTA 3: API PARA REGISTO (COM VALIDAÇÃO) ---
@app.route('/api/register', methods=['POST'])
def api_register():
    """Esta é a função que o JavaScript chama para criar uma nova conta."""
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    
    # Validações de Backend
    if not nome or not email or not senha:
        return jsonify({"success": False, "message": "Todos os campos são obrigatórios."})
    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"success": False, "message": "Formato de e-mail inválido."})
        
    if len(senha) < 8:
        return jsonify({"success": False, "message": "A senha deve ter pelo menos 8 caracteres."})
        
    if not re.search(r"\d", senha):
        return jsonify({"success": False, "message": "A senha deve conter pelo menos um número."})
        
    if not re.search(r"[A-Z]", senha):
        return jsonify({"success": False, "message": "A senha deve conter pelo menos uma letra maiúscula."})

    try:
        novo_usuario = {
            'nome': nome,
            'email': email,
            'senha_hash': hash_senha(senha),
            'tipo_conta': data.get('tipo_conta'),
            'telefone': data.get('telefone', ''),
            'data_registo': datetime.now().strftime("%Y-%m-%d")
        }
        requests.post(get_db_url('contas'), json=novo_usuario)
        return jsonify({"success": True, "message": "Registado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro no servidor: {e}"})

# --- ROTA 4: API PARA SERVIÇOS (GET, POST, DELETE) ---
@app.route('/api/servicos', methods=['GET'])
def api_get_servicos():
    resp = requests.get(get_db_url('servicos'))
    return jsonify(resp.json() or {})

@app.route('/api/servicos/add', methods=['POST'])
def api_add_servico():
    data = request.json
    requests.post(get_db_url('servicos'), json=data)
    return jsonify({"success": True, "message": "Serviço adicionado!"})

@app.route('/api/servicos/delete', methods=['POST'])
def api_delete_servico():
    data = request.json
    servico_id = data.get('id')
    if not servico_id:
        return jsonify({"success": False, "message": "ID do serviço em falta."})
    try:
        requests.delete(f"{FIREBASE_URL}/servicos/{servico_id}.json")
        return jsonify({"success": True, "message": "Serviço removido!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro no servidor: {e}"})


# --- ROTA 5: API PARA CONTAS (Funcionários, Clientes) (GET) ---
@app.route('/api/contas/<tipo_conta>', methods=['GET'])
def api_get_contas(tipo_conta):
    try:
        response = requests.get(get_db_url('contas'))
        contas = response.json() or {}
        # CORREÇÃO: Remove o 's' final do tipo (ex: 'clientes' -> 'cliente')
        filtro_tipo = tipo_conta.rstrip('s')
        contas_filtradas = {uid: conta for uid, conta in contas.items() 
                           if conta.get('tipo_conta') == filtro_tipo}
        return jsonify(contas_filtradas)
    except Exception as e:
        return jsonify({"error": str(e)})

# --- ROTA 6: API PARA AGENDAMENTOS (GET E POST) ---
@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    if request.method == 'GET':
        resp = requests.get(get_db_url('agendamentos'))
        return jsonify(resp.json() or {})
    
    elif request.method == 'POST':
        data = request.json
        
        # !! A CORREÇÃO ESTÁ AQUI !!
        data_val = data.get('data') # Ex: "2025-11-20"
        hora_val = data.get('hora') # Ex: "14:30"
        
        if not data_val or not hora_val:
            return jsonify({"success": False, "message": "Data ou hora em falta."})

        # O Backend junta a data e a hora
        data_hora_str = f"{data_val} {hora_val}" # Formato: "YYYY-MM-DD HH:MM"
        
        try:
            data_obj = datetime.strptime(data_hora_str, "%Y-%m-%d %H:%M")
            
            if data_obj < datetime.now():
                return jsonify({"success": False, "message": "Não pode agendar no passado."})
            if data_obj.weekday() == 6: # 6 é Domingo
                return jsonify({"success": False, "message": "Erro: O salão está fechado aos Domingos."})
            if not (9 <= data_obj.hour < 19):
                 return jsonify({"success": False, "message": "Erro: O horário de funcionamento é das 9:00 às 19:00."})

            agendamentos_existentes = requests.get(get_db_url('agendamentos')).json() or {}
            for ag in agendamentos_existentes.values():
                if (ag.get('data_agendamento') == data_hora_str and 
                    ag.get('id_funcionario') == data.get('id_funcionario') and 
                    ag.get('status') == 'agendado'):
                    return jsonify({"success": False, "message": "Erro: Este profissional já está ocupado nesse horário."})
                    
        except ValueError:
            return jsonify({"success": False, "message": "Formato de data inválido."})
        except Exception as e:
            return jsonify({"success": False, "message": f"Erro de validação: {e}"})
            
        data['status'] = 'agendado'
        # Salva a string completa que o backend criou
        data['data_agendamento'] = data_hora_str 
        # Remove as chaves separadas
        data.pop('data', None)
        data.pop('hora', None)
        
        requests.post(get_db_url('agendamentos'), json=data)
        return jsonify({"success": True, "message": "Agendado com sucesso!"})

# --- ROTA 7: API PARA ATUALIZAR AGENDA (Concluir/Cancelar) ---
@app.route('/api/agendamentos/update', methods=['POST'])
def api_update_agendamento():
    data = request.json
    ag_id = data.get('id')
    status = data.get('status')
    
    requests.patch(f"{FIREBASE_URL}/agendamentos/{ag_id}.json", json={'status': status})
    
    if status == 'concluido':
        ag = requests.get(f"{FIREBASE_URL}/agendamentos/{ag_id}.json").json()
        servicos = requests.get(get_db_url('servicos')).json() or {}
        
        comissao = 20 # Padrão
        if ag and 'id_servico' in ag and ag['id_servico'] in servicos:
            comissao = servicos[ag['id_servico']].get('comissao_percentual', 20)

        atendimento = {
            'id_funcionario': ag.get('id_funcionario'),
            'id_cliente': ag.get('id_cliente'),
            'nome_cliente': ag.get('nome_cliente'),
            'nome_servico': ag.get('nome_servico'),
            'valor_servico': ag.get('valor_servico'),
            'comissao_percentual': comissao / 100,
            'data': datetime.now().strftime("%Y-%m-%d")
        }
        requests.post(get_db_url('atendimentos'), json=atendimento)
            
    return jsonify({"success": True, "message": f"Agendamento {status}!"})

# --- ROTA 8: API PARA RELATÓRIOS (GERENTE) ---
@app.route('/api/relatorio/geral')
def api_relatorio_geral():
    atendimentos = requests.get(get_db_url('atendimentos')).json() or {}
    total, comissoes = 0, 0
    for at in atendimentos.values():
        total += at.get('valor_servico', 0)
        comissoes += at.get('valor_servico', 0) * at.get('comissao_percentual', 0)
    
    return jsonify({
        "faturamento_total": total,
        "total_comissoes": comissoes,
        "lucro_bruto": total - comissoes
    })
    
# --- ROTA 9: API PARA RELATÓRIO (FUNCIONÁRIO, individual) ---
@app.route('/api/relatorio/funcionario/<id_func>')
def api_relatorio_funcionario(id_func):
    atendimentos = requests.get(get_db_url('atendimentos')).json() or {}
    total, comissao = 0, 0
    for at in atendimentos.values():
        if at.get('id_funcionario') == id_func:
            total += 1
            comissao += at.get('valor_servico', 0) * at.get('comissao_percentual', 0)
    
    return jsonify({
        "total_atendimentos": total,
        "comissao_total": comissao
    })

# --- ROTA 10: API PARA ANÁLISE DE CLIENTE ---
@app.route('/api/analise/cliente/<id_cliente>')
def api_analise_cliente(id_cliente):
    atendimentos = requests.get(get_db_url('atendimentos')).json() or {}
    contas = requests.get(get_db_url('contas')).json() or {}
    
    cliente_info = contas.get(id_cliente, {})
    data_registo = cliente_info.get('data_registo', 'N/A')
    
    visitas = 0
    for at in atendimentos.values():
        if at.get('id_cliente') == id_cliente:
            visitas += 1
            
    frequencia_msg = "Cliente novo"
    if visitas > 5: frequencia_msg = "Cliente Regular"
    elif visitas > 1: frequencia_msg = "Cliente Recorrente"
    
    return jsonify({
        "total_visitas": visitas,
        "frequencia_msg": frequencia_msg,
        "cliente_desde": data_registo
    })
    
# --- Inicia o servidor ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
