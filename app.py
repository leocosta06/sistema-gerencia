from flask import Flask, request, jsonify, send_from_directory
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import secrets

app = Flask(__name__, template_folder='templates')

# === CONFIGS ===
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:8080')
GERENTE_TOKEN = os.environ.get('GERENTE_TOKEN', 'leonardo123')

# === BANCO DE DADOS SIMULADO ===
usuarios = {
    "leonardocalmeida2@gmail.com": {
        "id": 1,
        "nome": "Leonardo Almeida",
        "senha": "Demo123456",
        "tipo_conta": "gerente"
    }
}

agendamentos = {}
servicos = {
    "1": {"nome": "Corte Masculino", "valor": 50.0, "comissao_percentual": 30}
}

tokens_recuperacao = {}

# === FUNÇÃO DE E-MAIL ===
def enviar_email_recuperacao(email, token):
    if not EMAIL_USER or not EMAIL_PASS:
        app.logger.warning("E-mail não configurado!")
        return False

    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = email
    msg['Subject'] = "Redefinição de Senha - SalãoApp"

    link = f"https://{RENDER_HOST}/redefinir-senha?token={token}"
    corpo = f"""
    <h2>Redefinição de Senha</h2>
    <p>Clique no link para redefinir sua senha:</p>
    <p><a href="{link}" style="color:#2563eb;font-weight:bold;text-decoration:underline;">{link}</a></p>
    <p><strong>Expira em 15 minutos.</strong></p>
    <p>Se não solicitou, ignore.</p>
    <hr><small>SalãoApp</small>
    """
    msg.attach(MIMEText(corpo, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        return True
    except Exception as e:
        app.logger.error(f"Erro e-mail: {e}")
        return False

# === ROTAS ESTÁTICAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/redefinir-senha')
def pagina_redefinir():
    return send_from_directory('templates', 'index.html')

# === AUTENTICAÇÃO ===
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    user = usuarios.get(email)
    if user and user['senha'] == senha:
        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "nome": user["nome"],
                "tipo_conta": user["tipo_conta"]
            }
        })
    return jsonify({"success": False, "message": "E-mail ou senha incorretos."})

@app.route('/api/cadastrar', methods=['POST'])
def api_cadastrar():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    nome = data.get('nome')
    tipo_conta = data.get('tipo_conta', 'funcionario')
    token_gerente = data.get('token_gerente')

    if not all([email, senha, nome]):
        return jsonify({"success": False, "message": "Preencha todos os campos."})

    if email in usuarios:
        return jsonify({"success": False, "message": "E-mail já cadastrado."})

    if len(senha) < 6:
        return jsonify({"success": False, "message": "Senha deve ter 6+ caracteres."})

    if tipo_conta not in ['gerente', 'funcionario']:
        return jsonify({"success": False, "message": "Tipo inválido."})

    if tipo_conta == 'gerente' and token_gerente != GERENTE_TOKEN:
        return jsonify({"success": False, "message": "Token de gerente inválido."})

    novo_id = max([u["id"] for u in usuarios.values()], default=0) + 1
    usuarios[email] = {
        "id": novo_id,
        "nome": nome,
        "senha": senha,
        "tipo_conta": tipo_conta
    }

    return jsonify({
        "success": True,
        "message": "Cadastro realizado!",
        "user": {"id": novo_id, "nome": nome, "tipo_conta": tipo_conta}
    })

# === RECUPERAÇÃO DE SENHA ===
@app.route('/api/recuperar-senha', methods=['POST'])
def api_recuperar_senha():
    data = request.get_json()
    email = data.get('email')
    if email not in usuarios:
        return jsonify({"success": False, "message": "E-mail não encontrado."})

    token = secrets.token_urlsafe(32)
    tokens_recuperacao[token] = {"email": email, "expira": datetime.now().timestamp() + 900}

    if enviar_email_recuperacao(email, token):
        return jsonify({"success": True, "message": "Link enviado!"})
    return jsonify({"success": False, "message": "Erro ao enviar."})

@app.route('/api/redefinir-senha', methods=['POST'])
def api_redefinir_senha():
    data = request.get_json()
    token = data.get('token')
    nova_senha = data.get('nova_senha')

    if token not in tokens_recuperacao:
        return jsonify({"success": False, "message": "Token inválido."})

    info = tokens_recuperacao[token]
    if datetime.now().timestamp() > info["expira"]:
        del tokens_recuperacao[token]
        return jsonify({"success": False, "message": "Token expirado."})

    usuarios[info["email"]]["senha"] = nova_senha
    del tokens_recuperacao[token]
    return jsonify({"success": True, "message": "Senha alterada!"})

# === SERVIÇOS ===
@app.route('/api/servicos', methods=['GET'])
def api_listar_servicos():
    return jsonify(servicos)

@app.route('/api/servicos', methods=['POST'])
def api_adicionar_servico():
    data = request.get_json()
    nome = data.get('nome')
    valor = data.get('valor')
    comissao = data.get('comissao_percentual')

    if not all([nome, valor, comissao]):
        return jsonify({"success": False, "message": "Preencha todos os campos."})

    novo_id = str(max([int(k) for k in servicos.keys()], default=0) + 1)
    servicos[novo_id] = {
        "nome": nome,
        "valor": float(valor),
        "comissao_percentual": int(comissao)
    }
    return jsonify({"success": True, "id": novo_id})

@app.route('/api/servicos/<id>', methods=['DELETE'])
def api_apagar_servico(id):
    if id in servicos:
        del servicos[id]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Serviço não encontrado."})

# === AGENDAMENTOS ===
@app.route('/api/agendamentos', methods=['GET'])
def api_listar_agendamentos():
    return jsonify(agendamentos)

@app.route('/api/agendamentos', methods=['POST'])
def api_criar_agendamento():
    data = request.get_json()
    servico_id = data.get('servico_id')
    data_hora = data.get('data_hora')  # "2025-11-18 10:00"
    cliente_nome = data.get('cliente_nome')
    funcionario_id = data.get('funcionario_id', 1)

    if not all([servico_id, data_hora, cliente_nome]):
        return jsonify({"success": False, "message": "Dados incompletos."})

    if servico_id not in servicos:
        return jsonify({"success": False, "message": "Serviço inválido."})

    novo_id = str(max([int(k) for k in agendamentos.keys()], default=0) + 1)
    agendamentos[novo_id] = {
        "id": novo_id,
        "servico_id": servico_id,
        "nome_servico": servicos[servico_id]["nome"],
        "valor": servicos[servico_id]["valor"],
        "comissao_percentual": servicos[servico_id]["comissao_percentual"],
        "data_agendamento": data_hora,
        "nome_cliente": cliente_nome,
        "funcionario_id": funcionario_id,
        "status": "agendado"
    }
    return jsonify({"success": True, "id": novo_id})

@app.route('/api/agendamentos/<id>/concluir', methods=['PATCH'])
def api_concluir_agendamento(id):
    if id not in agendamentos:
        return jsonify({"success": False, "message": "Agendamento não encontrado."})
    agendamentos[id]["status"] = "concluido"
    return jsonify({"success": True})

# === CONTAS (GERENTE) ===
@app.route('/api/contas', methods=['GET'])
def api_listar_contas():
    return jsonify(usuarios)

@app.route('/api/contas', methods=['POST'])
def api_criar_conta_admin():
    data = request.get_json()
    return api_cadastrar().get_json()  # Reutiliza cadastro

@app.route('/api/contas/<email>', methods=['DELETE'])
def api_apagar_conta(email):
    if email not in usuarios:
        return jsonify({"success": False, "message": "Usuário não encontrado."})
    if usuarios[email]["tipo_conta"] == "gerente" and len([u for u in usuarios.values() if u["tipo_conta"] == "gerente"]) == 1:
        return jsonify({"success": False, "message": "Não pode apagar o último gerente."})
    del usuarios[email]
    return jsonify({"success": True})

# === RELATÓRIOS (GERENTE) ===
@app.route('/api/relatorios/financeiro')
def api_relatorio_financeiro():
    concluidos = [a for a in agendamentos.values() if a["status"] == "concluido"]
    faturamento = sum(a["valor"] for a in concluidos)
    comissoes = sum(a["valor"] * a["comissao_percentual"] / 100 for a in concluidos)
    lucro = faturamento - comissoes
    return jsonify({
        "faturamento": round(faturamento, 2),
        "comissoes": round(comissoes, 2),
        "lucro": round(lucro, 2)
    })

# === FUNCIONÁRIOS ===
@app.route('/api/funcionarios')
def api_funcionarios():
    funcs = {email: u for email, u in usuarios.items() if u["tipo_conta"] == "funcionario"}
    return jsonify(funcs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))