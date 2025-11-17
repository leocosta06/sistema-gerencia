from flask import Flask, request, jsonify, render_template, send_from_directory
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
        "senha": "Demo123456",  # hash em produção
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
    <p>
        <a href="{link}" style="color: #2563eb; text-decoration: underline; font-weight: bold;">
            {link}
        </a>
    </p>
    <p><strong>Expira em 15 minutos.</strong></p>
    <p>Se não solicitou, ignore este e-mail.</p>
    <hr>
    <p style="font-size: 12px; color: #999;">SalãoApp - Sistema de Gestão</p>
    """
    msg.attach(MIMEText(corpo, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        app.logger.info(f"E-mail enviado para {email}")
        return True
    except Exception as e:
        app.logger.error(f"Erro ao enviar e-mail: {e}")
        return False

# === ROTAS ESTÁTICAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/redefinir-senha')
def pagina_redefinir():
    return send_from_directory('templates', 'index.html')

# === API LOGIN ===
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

# === CADASTRO DE NOVA CONTA ===
@app.route('/api/cadastrar', methods=['POST'])
def api_cadastrar():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    nome = data.get('nome')
    tipo_conta = data.get('tipo_conta', 'funcionario')

    # Validações
    if not email or not senha or not nome:
        return jsonify({"success": False, "message": "Preencha todos os campos."})

    if email in usuarios:
        return jsonify({"success": False, "message": "E-mail já cadastrado."})

    if len(senha) < 6:
        return jsonify({"success": False, "message": "A senha deve ter pelo menos 6 caracteres."})

    if tipo_conta not in ['gerente', 'funcionario']:
        return jsonify({"success": False, "message": "Tipo de conta inválido."})

    # Só gerente pode criar outro gerente
    if tipo_conta == 'gerente':
        token_fornecido = data.get('token_gerente')
        if token_fornecido != GERENTE_TOKEN:
            return jsonify({"success": False, "message": "Token de gerente inválido."})

    # Cria usuário
    novo_id = max([u["id"] for u in usuarios.values()], default=0) + 1
    usuarios[email] = {
        "id": novo_id,
        "nome": nome,
        "senha": senha,
        "tipo_conta": tipo_conta
    }

    app.logger.info(f"Novo usuário cadastrado: {email} ({tipo_conta})")

    return jsonify({
        "success": True,
        "message": "Cadastro realizado com sucesso!",
        "user": {
            "id": novo_id,
            "nome": nome,
            "tipo_conta": tipo_conta
        }
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
        return jsonify({"success": True, "message": "Link enviado! Verifique seu e-mail."})
    else:
        return jsonify({"success": False, "message": "Erro ao enviar e-mail."})

# === REDEFINIR SENHA ===
@app.route('/api/redefinir-senha', methods=['POST'])
def api_redefinir_senha():
    data = request.get_json()
    token = data.get('token')
    nova_senha = data.get('nova_senha')

    if token not in tokens_recuperacao:
        return jsonify({"success": False, "message": "Token inválido ou expirado."})

    info = tokens_recuperacao[token]
    if datetime.now().timestamp() > info["expira"]:
        del tokens_recuperacao[token]
        return jsonify({"success": False, "message": "Token expirado."})

    email = info["email"]
    usuarios[email]["senha"] = nova_senha
    del tokens_recuperacao[token]

    return jsonify({"success": True, "message": "Senha alterada com sucesso!"})

# === OUTRAS ROTAS (simuladas) ===
@app.route('/api/servicos')
def api_servicos():
    return jsonify(servicos)

@app.route('/api/agendamentos')
def api_agendamentos():
    return jsonify(agendamentos)

@app.route('/api/contas/funcionarios')
def api_funcionarios():
    funcs = {email: u for email, u in usuarios.items() if u["tipo_conta"] == "funcionario"}
    return jsonify(funcs)

@app.route('/api/contas/todos')
def api_todas_contas():
    return jsonify(usuarios)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))