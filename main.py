from flask import Flask, render_template, request, jsonify
import requests
import hashlib
from datetime import datetime
import os

# Configura a aplicação Flask
# 'template_folder' diz ao Flask para procurar o HTML na pasta 'templates'
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
    # Garante que a URL não termina com uma barra extra
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

# --- ROTA 3: API PARA REGISTO ---
@app.route('/api/register', methods=['POST'])
def api_register():
    """Esta é a função que o JavaScript chama para criar uma nova conta."""
    data = request.json
    try:
        novo_usuario = {
            'nome': data.get('nome'),
            'email': data.get('email'),
            'senha_hash': hash_senha(data.get('senha')),
            'tipo_conta': data.get('tipo_conta'),
            'telefone': data.get('telefone', ''), # Opcional
            'data_registo': datetime.now().strftime("%Y-%m-%d")
        }
        # Envia os dados para o Firebase
        requests.post(get_db_url('contas'), json=novo_usuario)
        return jsonify({"success": True, "message": "Registado com sucesso!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Erro no servidor: {e}"})

# --- ROTA 4: API PARA SERVIÇOS (GET E POST) ---
@app.route('/api/servicos', methods=['GET', 'POST'])
def api_servicos():
    """Função para o Gerente ler ou adicionar novos serviços."""
    if request.method == 'GET':
        resp = requests.get(get_db_url('servicos'))
        return jsonify(resp.json() or {})
    
    elif request.method == 'POST':
        data = request.json # {nome, valor, comissao}
        requests.post(get_db_url('servicos'), json=data)
        return jsonify({"success": True, "message": "Serviço adicionado!"})

# --- ROTA 5: API PARA AGENDAMENTOS (GET E POST) ---
@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    """Função para o Cliente ler ou criar agendamentos."""
    if request.method == 'GET':
        resp = requests.get(get_db_url('agendamentos'))
        return jsonify(resp.json() or {})
    
    elif request.method == 'POST':
        data = request.json
        data['status'] = 'agendado' # Define o status inicial
        requests.post(get_db_url('agendamentos'), json=data)
        return jsonify({"success": True, "message": "Agendado com sucesso!"})

# --- ROTA 6: API PARA ATUALIZAR AGENDA ---
@app.route('/api/agendamentos/update', methods=['POST'])
def api_update_agendamento():
    """Função para o Gerente atualizar o status (Concluir/Cancelar)."""
    data = request.json
    ag_id = data.get('id')
    status = data.get('status')
    
    # Atualiza o status no Firebase
    requests.patch(f"{FIREBASE_URL}/agendamentos/{ag_id}.json", json={'status': status})
    
    # Se o status for "concluido", cria um registo de atendimento
    if status == 'concluido':
        ag = requests.get(f"{FIREBASE_URL}/agendamentos/{ag_id}.json").json()
        servicos = requests.get(get_db_url('servicos')).json() or {}
        
        comissao = 20 # Padrão
        if ag.get('id_servico') in servicos:
            comissao = servicos[ag['id_servico']].get('comissao_percentual', 20)

        atendimento = {
            'id_funcionario': ag.get('id_funcionario'),
            'id_cliente': ag.get('id_cliente'),
            'nome_servico': ag.get('nome_servico'),
            'valor_servico': ag.get('valor_servico'),
            'comissao_percentual': comissao / 100,
            'data': datetime.now().strftime("%Y-%m-%d")
        }
        requests.post(get_db_url('atendimentos'), json=atendimento)
            
    return jsonify({"success": True})

# --- ROTA 7: API PARA RELATÓRIOS (GERENTE) ---
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
    
# --- ROTA 8: API PARA RELATÓRIO (FUNCIONÁRIO) ---
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
    
# --- Inicia o servidor ---
if __name__ == '__main__':
    # 'host' e 'port' são necessários para o Replit
    app.run(host='0.0.0.0', port=8080)
