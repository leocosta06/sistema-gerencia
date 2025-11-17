from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import secrets

app = Flask(__name__, template_folder='templates')

# === CONFIGS ===
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:8080')
GERENTE_TOKEN = os.environ.get('GERENTE_TOKEN', 'leonardo123')

# === BANCO DE DADOS SIMULADO ===
usuarios = {
    "leonardocalmeida2@gmail.com": {
        "id": 1,
        "nome": "DEMO",
        "senha": "Demo123456",
        "tipo_conta": "gerente"
    }
}

agendamentos = {}
servicos = {
    "1": {"nome": "Corte Masculino", "valor": 50.0, "comissao_percentual": 30}
}

# === ROTAS ESTÁTICAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/redefinir-senha')
def pagina_redefinir():
    return send_from_directory('templates', 'index.html')

# === LOGIN ===
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    # MODO DEMO
    if email == "demo@salao.com" and senha == "demo":
        return jsonify({
            "success": True,
            "user": {
                "id": 999,
                "nome": "Demo Gerente",
                "tipo_conta": "gerente"
            },
            "demo": True
        })

    user = usuarios.get(email)
    if user and user['senha'] == senha:
        return jsonify({
            "success": True,
            "user": {
                "id": user["id"],
                "nome": user["nome"],
                "tipo_conta": user["tipo_conta"]
            },
            "demo": False
        })
    return jsonify({"success": False, "message": "E-mail ou senha incorretos."})

# === CADASTRO (CLIENTE, FUNCIONÁRIO, GERENTE) ===
@app.route('/api/cadastrar', methods=['POST'])
def api_cadastrar():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')
    nome = data.get('nome')
    tipo_conta = data.get('tipo_conta', 'cliente')
    token_gerente = data.get('token_gerente')

    if not all([email, senha, nome]):
        return jsonify({"success": False, "message": "Preencha todos os campos."})

    if email in usuarios:
        return jsonify({"success": False, "message": "E-mail já cadastrado."})

    if len(senha) < 6:
        return jsonify({"success": False, "message": "Senha deve ter 6+ caracteres."})

    if tipo_conta not in ['cliente', 'funcionario', 'gerente']:
        return jsonify({"success": False, "message": "Tipo inválido."})

    if tipo_conta == 'gerente' and token_gerente != GERENTE_TOKEN:
        return jsonify({"success": False, "message": "Token inválido."})

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

# === RECUPERAÇÃO DE SENHA (TEMPORARIAMENTE DESATIVADA) ===
# @app.route('/api/recuperar-senha', methods=['POST'])
# def api_recuperar_senha():
#     return jsonify({"success": False, "message": "Recuperação de senha temporariamente desativada."})
#
# @app.route('/api/redefinir-senha', methods=['POST'])
# def api_redefinir_senha():
#     return jsonify({"success": False, "message": "Recuperação de senha temporariamente desativada."})

# === SERVIÇOS ===
@app.route('/api/servicos', methods=['GET', 'POST'])
def api_servicos():
    if request.method == 'GET':
        return jsonify(servicos)

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
@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    if request.method == 'GET':
        return jsonify(agendamentos)

    data = request.get_json()
    servico_id = data.get('servico_id')
    data_hora = data.get('data_hora')
    cliente_id = data.get('cliente_id')
    funcionario_id = data.get('funcionario_id', 1)

    if not all([servico_id, data_hora, cliente_id]):
        return jsonify({"success": False, "message": "Dados incompletos."})

    if servico_id not in servicos:
        return jsonify({"success": False, "message": "Serviço inválido."})

    novo_id = str(max([int(k) for k in agendamentos.keys()], default=0) + 1)
    cliente = next((u for u in usuarios.values() if u["id"] == int(cliente_id)), None)
    agendamentos[novo_id] = {
        "id": novo_id,
        "servico_id": servico_id,
        "nome_servico": servicos[servico_id]["nome"],
        "valor": servicos[servico_id]["valor"],
        "comissao_percentual": servicos[servico_id]["comissao_percentual"],
        "data_agendamento": data_hora,
        "cliente_id": cliente_id,
        "nome_cliente": cliente["nome"] if cliente else "Cliente",
        "funcionario_id": funcionario_id,
        "status": "agendado"
    }
    return jsonify({"success": True, "id": novo_id})

@app.route('/api/agendamentos/<id>/concluir', methods=['PATCH'])
def api_concluir_agendamento(id):
    if id not in agendamentos:
        return jsonify({"success": False, "message": "Não encontrado."})
    agendamentos[id]["status"] = "concluido"
    return jsonify({"success": True})

# === RELATÓRIOS ===
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

@app.route('/api/relatorios/funcionario/<int:func_id>')
def api_relatorio_funcionario(func_id):
    atendimentos = [a for a in agendamentos.values() if a["funcionario_id"] == func_id and a["status"] == "concluido"]
    total_comissao = sum(a["valor"] * a["comissao_percentual"] / 100 for a in atendimentos)
    return jsonify({
        "comissao": round(total_comissao, 2),
        "atendimentos": len(atendimentos)
    })

# === CONTAS ===
@app.route('/api/contas', methods=['GET', 'POST'])
def api_contas():
    if request.method == 'GET':
        return jsonify(usuarios)
    return api_cadastrar().get_json()

@app.route('/api/contas/<email>', methods=['DELETE'])
def api_apagar_conta(email):
    if email not in usuarios:
        return jsonify({"success": False, "message": "Não encontrado."})
    if usuarios[email]["tipo_conta"] == "gerente" and len([u for u in usuarios.values() if u["tipo_conta"] == "gerente"]) == 1:
        return jsonify({"success": False, "message": "Não pode apagar o último gerente."})
    del usuarios[email]
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))