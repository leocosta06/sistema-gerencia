from flask import Flask, request, jsonify, send_from_directory
import requests
import hashlib
import re
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import logging

app = Flask(__name__, static_folder='templates', static_url_path='')

# === CONFIGURAÇÕES ===
logging.basicConfig(level=logging.DEBUG)
FIREBASE_URL = os.environ.get('FIREBASE_URL', 'https://sistema-salao-59ac8-default-rtdb.firebaseio.com')
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:8080')

# === FUNÇÕES AUXILIARES ===
def get_db_url(path):
    return f"{FIREBASE_URL}/{path}.json"

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def enviar_email_recuperacao(email, token):
    if not EMAIL_USER or not EMAIL_PASS:
        app.logger.warning("E-mail não configurado (EMAIL_USER/PASS)")
        return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = email
    msg['Subject'] = "Redefinição de Senha - SalãoApp"
    
    link = f"https://{RENDER_HOST}/redefinir-senha?token={token}"
    corpo = f"""
    <h2>Redefinição de Senha</h2>
    <p>Clique no link para redefinir sua senha:</p>
    <p><a href="{link}" style="color: blue;">{link}</a></p>
    <p>Este link expira em 15 minutos.</p>
    <p>Se você não solicitou, ignore este e-mail.</p>
    """
    msg.attach(MIMEText(corpo, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        app.logger.info(f"E-mail enviado para {email}")
    except Exception as e:
        app.logger.error(f"Erro ao enviar e-mail: {e}")

# === ROTAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

# === LOGIN ===
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')
    if not email or not senha:
        return jsonify({"success": False, "message": "Preencha e-mail e senha."})

    contas = requests.get(get_db_url('contas')).json() or {}
    for uid, user in contas.items():
        if user.get('email') == email and user.get('senha_hash') == hash_senha(senha):
            user_data = user.copy()
            user_data['id'] = uid
            return jsonify({"success": True, "user": user_data})
    return jsonify({"success": False, "message": "E-mail ou senha incorretos."})

# === CADASTRO ===
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    telefone = data.get('telefone', '')

    if not all([nome, email, senha]):
        return jsonify({"success": False, "message": "Preencha nome, e-mail e senha."})
    if len(senha) < 8 or not re.search(r'\d', senha) or not re.search(r'[A-Z]', senha):
        return jsonify({"success": False, "message": "Senha: 8+ caracteres, 1 número, 1 maiúscula."})
    if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        return jsonify({"success": False, "message": "E-mail inválido."})

    contas = requests.get(get_db_url('contas')).json() or {}
    if any(c.get('email') == email for c in contas.values()):
        return jsonify({"success": False, "message": "E-mail já cadastrado."})

    novo_usuario = {
        'nome': nome,
        'email': email,
        'senha_hash': hash_senha(senha),
        'tipo_conta': 'cliente',
        'telefone': telefone,
        'data_registo': datetime.now().strftime("%Y-%m-%d")
    }
    res = requests.post(get_db_url('contas'), json=novo_usuario)
    if res.status_code == 200:
        return jsonify({"success": True, "message": "Conta criada! Faça login."})
    return jsonify({"success": False, "message": "Erro ao salvar."})

# === RECUPERAÇÃO DE SENHA ===
@app.route('/api/recuperar-senha', methods=['POST'])
def api_recuperar_senha():
    email = request.json.get('email')
    if not email:
        return jsonify({"success": False, "message": "E-mail obrigatório."})

    contas = requests.get(get_db_url('contas')).json() or {}
    uid = next((id_ for id_, c in contas.items() if c.get('email') == email), None)
    if not uid:
        return jsonify({"success": False, "message": "E-mail não encontrado."})

    token = secrets.token_urlsafe(32)
    expiracao = (datetime.now() + timedelta(minutes=15)).isoformat()
    requests.patch(f"{FIREBASE_URL}/recuperacao_senha/{uid}.json", json={'token': token, 'expiracao': expiracao})
    enviar_email_recuperacao(email, token)
    return jsonify({"success": True, "message": "Link enviado! Verifique seu e-mail."})

@app.route('/api/redefinir-senha', methods=['POST'])
def api_redefinir_senha():
    token = request.json.get('token')
    nova_senha = request.json.get('nova_senha')
    if len(nova_senha) < 8:
        return jsonify({"success": False, "message": "Senha muito curta."})

    tokens = requests.get(get_db_url('recuperacao_senha')).json() or {}
    for uid, info in tokens.items():
        if info.get('token') == token:
            exp = datetime.fromisoformat(info['expiracao'])
            if datetime.now() > exp:
                return jsonify({"success": False, "message": "Token expirado."})
            nova_hash = hash_senha(nova_senha)
            requests.patch(f"{FIREBASE_URL}/contas/{uid}.json", json={'senha_hash': nova_hash})
            requests.delete(f"{FIREBASE_URL}/recuperacao_senha/{uid}.json")
            return jsonify({"success": True, "message": "Senha alterada com sucesso!"})
    return jsonify({"success": False, "message": "Token inválido."})

# === GERENTE ===
def verificar_gerente():
    auth = request.headers.get('Authorization')
    return auth == 'Bearer gerente-secreto-temporario'

@app.route('/api/contas/todos', methods=['GET'])
def api_get_todas_contas():
    if not verificar_gerente():
        return jsonify({"success": False, "message": "Acesso negado."}), 403
    return jsonify(requests.get(get_db_url('contas')).json() or {})

@app.route('/api/contas/criar', methods=['POST'])
def api_criar_conta():
    if not verificar_gerente():
        return jsonify({"success": False, "message": "Apenas gerentes."}), 403
    data = request.json
    tipo = data.get('tipo_conta')
    if tipo not in ['funcionario', 'gerente']:
        return jsonify({"success": False, "message": "Tipo inválido."})
    novo = {
        'nome': data['nome'],
        'email': data['email'],
        'senha_hash': hash_senha(data['senha']),
        'tipo_conta': tipo,
        'data_registo': datetime.now().strftime("%Y-%m-%d")
    }
    res = requests.post(get_db_url('contas'), json=novo)
    return jsonify({"success": res.status_code == 200})

@app.route('/api/contas/apagar', methods=['POST'])
def api_apagar_conta():
    if not verificar_gerente():
        return jsonify({"success": False, "message": "Acesso negado."}), 403
    uid = request.json.get('id')
    requests.delete(f"{FIREBASE_URL}/contas/{uid}.json")
    return jsonify({"success": True})

# === SERVIÇOS ===
@app.route('/api/servicos', methods=['GET', 'POST'])
def api_servicos():
    if request.method == 'GET':
        return jsonify(requests.get(get_db_url('servicos')).json() or {})
    data = request.json
    res = requests.post(get_db_url('servicos'), json=data)
    return jsonify({"success": res.status_code == 200})

@app.route('/api/servicos/delete', methods=['POST'])
def api_del_servico():
    uid = request.json.get('id')
    requests.delete(f"{FIREBASE_URL}/servicos/{uid}.json")
    return jsonify({"success": True})

# === AGENDAMENTOS ===
@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    if request.method == 'GET':
        return jsonify(requests.get(get_db_url('agendamentos')).json() or {})

    data = request.json
    data_val = data.get('data_agendamento')
    try:
        inicio_novo = datetime.strptime(data_val, "%Y-%m-%d %H:%M:%S")
        fim_novo = inicio_novo + timedelta(hours=1)
        agora = datetime.now()

        if inicio_novo < agora:
            return jsonify({"success": False, "message": "Não pode agendar no passado."})
        if inicio_novo.weekday() == 6:
            return jsonify({"success": False, "message": "Fechado aos domingos."})
        if not (9 <= inicio_novo.hour < 19):
            return jsonify({"success": False, "message": "Funcionamento: 9h às 19h."})

        agendamentos = requests.get(get_db_url('agendamentos')).json() or {}
        for ag in agendamentos.values():
            if ag.get('status') != 'agendado': continue
            try:
                inicio_exist = datetime.strptime(ag.get('data_agendamento'), "%Y-%m-%d %H:%M:%S")
                fim_exist = inicio_exist + timedelta(hours=1)
                if (ag.get('id_funcionario') == data.get('id_funcionario') and
                    inicio_novo < fim_exist and inicio_exist < fim_novo):
                    return jsonify({"success": False, "message": "Horário em conflito."})
            except:
                continue

        data['status'] = 'agendado'
        requests.post(get_db_url('agendamentos'), json=data)
        return jsonify({"success": True, "message": "Agendado com sucesso!"})
    except Exception as e:
        app.logger.error(f"Erro: {e}")
        return jsonify({"success": False, "message": "Erro no formato da data."})

@app.route('/api/agendamentos/update', methods=['POST'])
def api_update_agendamento():
    data = request.json
    uid = data.get('id')
    status = data.get('status')
    requests.patch(f"{FIREBASE_URL}/agendamentos/{uid}.json", json={'status': status})
    return jsonify({"success": True})

# === RELATÓRIOS ===
@app.route('/api/relatorio/geral')
def relatorio_geral():
    agendamentos = requests.get(get_db_url('agendamentos')).json() or {}
    concluido = [a for a in agendamentos.values() if a.get('status') == 'concluido']
    faturamento = sum(a.get('valor_servico', 0) for a in concluido)
    comissoes = sum(a.get('valor_servico', 0) * a.get('comissao_percentual', 0) / 100 for a in concluido)
    return jsonify({
        "faturamento_total": faturamento,
        "total_comissoes": comissoes,
        "lucro_bruto": faturamento - comissoes
    })

@app.route('/api/relatorio/funcionario/<func_id>')
def relatorio_func(func_id):
    agendamentos = requests.get(get_db_url('agendamentos')).json() or {}
    do_func = [a for a in agendamentos.values() if a.get('id_funcionario') == func_id and a.get('status') == 'concluido']
    total = len(do_func)
    comissao = sum(a.get('valor_servico', 0) * a.get('comissao_percentual', 0) / 100 for a in do_func)
    return jsonify({"total_atendimentos": total, "comissao_total": comissao})

@app.route('/api/analise/cliente/<cli_id>')
def analise_cliente(cli_id):
    agendamentos = requests.get(get_db_url('agendamentos')).json() or {}
    do_cli = [a for a in agendamentos.values() if a.get('id_cliente') == cli_id]
    total = len(do_cli)
    msg = "Fiel" if total > 5 else "Ocasional" if total > 1 else "Novo"
    return jsonify({"total_visitas": total, "frequencia_msg": msg})

@app.route('/api/contas/<tipo_conta>')
def api_contas_por_tipo(tipo_conta):
    contas = requests.get(get_db_url('contas')).json() or {}
    return jsonify({k: v for k, v in contas.items() if v.get('tipo_conta') == tipo_conta.rstrip('s')})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
