from flask import Flask, request, jsonify, send_from_directory
import os
from datetime import datetime
import secrets

app = Flask(__name__, template_folder='templates')

# === CONFIGS ===
RENDER_HOST = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:8080')
GERENTE_TOKEN = os.environ.get('GERENTE_TOKEN', 'leonardo123')

# === BANCO DE DADOS SIMULADO (COM DADOS DE DEMO) ===
# Estes dados estão em memória. Eles VÃO resetar se o backend for reiniciado.
# Esta é a "Demo via Backend".
usuarios = {
    "leonardocalmeida2@gmail.com": {
        "id": 1,
        "nome": "Leonardo Almeida",
        "senha": "Demo123456", # Em produção, use hashes
        "tipo_conta": "gerente"
    },
    "func1@salao.com": {
        "id": 2,
        "nome": "Maria Silva",
        "senha": "func123",
        "tipo_conta": "funcionario"
    },
    "cliente1@salao.com": {
        "id": 3,
        "nome": "João Pedro",
        "senha": "cli123",
        "tipo_conta": "cliente"
    }
}

agendamentos = {
    "1": {
        "id": "1",
        "servico_id": "1",
        "nome_servico": "Corte Masculino",
        "valor": 50.0,
        "comissao_percentual": 30,
        "data_agendamento": "2025-11-17 10:00", # Formato ISO (YYYY-MM-DD HH:MM)
        "cliente_id": 3,
        "nome_cliente": "João Pedro",
        "funcionario_id": 2,
        "status": "concluido" # Status: agendado, concluido, cancelado
    },
    "2": {
        "id": "2",
        "servico_id": "1",
        "nome_servico": "Corte Masculino",
        "valor": 50.0,
        "comissao_percentual": 30,
        "data_agendamento": "2025-11-17 14:00",
        "cliente_id": 3,
        "nome_cliente": "João Pedro",
        "funcionario_id": 2,
        "status": "agendado"
    }
}

servicos = {
    "1": {"id": "1", "nome": "Corte Masculino", "valor": 50.0, "comissao_percentual": 30},
    "2": {"id": "2", "nome": "Barba", "valor": 30.0, "comissao_percentual": 40},
    "3": {"id": "3", "nome": "Corte + Barba", "valor": 70.0, "comissao_percentual": 35}
}

# === ROTAS ESTÁTICAS ===
# Servir o index.html principal
@app.route('/')
def index():
    # Isso assume que seu 'index.html' do frontend estará na pasta 'templates'
    return send_from_directory('templates', 'index.html')

# Rota para permitir que o React Router (ou similar) controle o frontend
@app.route('/redefinir-senha')
def pagina_redefinir():
    return send_from_directory('templates', 'index.html')

# === LOGIN (COM DEMO) ===
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    # MODO DEMO
    if email == "demo@salao.com" and senha == "demo":
        return jsonify({
            "success": True,
            "user": {"id": 999, "nome": "Demo", "tipo_conta": "gerente"},
            "demo": True
        })

    user = usuarios.get(email)
    if user and user['senha'] == senha:
        return jsonify({
            "success": True,
            "user": {"id": user["id"], "nome": user["nome"], "tipo_conta": user["tipo_conta"]},
            "demo": False
        })
    return jsonify({"success": False, "message": "E-mail ou senha incorretos."})

# === CADASTRO ===
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

# === SERVIÇOS (CRUD) ===
@app.route('/api/servicos', methods=['GET', 'POST'])
def api_servicos():
    if request.method == 'GET':
        return jsonify(list(servicos.values())) # Retorna uma lista de objetos

    data = request.get_json()
    nome = data.get('nome')
    valor = data.get('valor')
    comissao = data.get('comissao_percentual')

    if not all([nome, valor, comissao]):
        return jsonify({"success": False, "message": "Preencha todos os campos."})

    novo_id = str(max([int(k) for k in servicos.keys()], default=0) + 1)
    servicos[novo_id] = {
        "id": novo_id, 
        "nome": nome,
        "valor": float(valor),
        "comissao_percentual": int(comissao)
    }
    return jsonify({"success": True, "servico": servicos[novo_id]})

@app.route('/api/servicos/<id>', methods=['DELETE', 'PUT'])
def api_servico_detalhe(id):
    if id not in servicos:
        return jsonify({"success": False, "message": "Serviço não encontrado."}), 404

    if request.method == 'DELETE':
        del servicos[id]
        return jsonify({"success": True})

    if request.method == 'PUT':
        data = request.get_json()
        servicos[id]["nome"] = data.get('nome', servicos[id]["nome"])
        servicos[id]["valor"] = float(data.get('valor', servicos[id]["valor"]))
        servicos[id]["comissao_percentual"] = int(data.get('comissao_percentual', servicos[id]["comissao_percentual"]))
        return jsonify({"success": True, "servico": servicos[id]})

# === AGENDAMENTOS (CRUD) ===
@app.route('/api/agendamentos', methods=['GET', 'POST'])
def api_agendamentos():
    if request.method == 'GET':
        return jsonify(list(agendamentos.values()))

    data = request.get_json()
    servico_id = data.get('servico_id')
    data_hora = data.get('data_hora') 
    cliente_id = data.get('cliente_id')
    funcionario_id = data.get('funcionario_id', 2) # Default para funcionário 2 (Maria Silva)

    if not all([servico_id, data_hora, cliente_id]):
        return jsonify({"success": False, "message": "Dados incompletos."})

    if servico_id not in servicos:
        return jsonify({"success": False, "message": "Serviço inválido."})

    email_cliente = next((e for e, u in usuarios.items() if u["id"] == int(cliente_id)), None)
    if not email_cliente:
         return jsonify({"success": False, "message": "Cliente inválido."})
         
    cliente = usuarios[email_cliente]
    servico = servicos[servico_id]

    novo_id = str(max([int(k) for k in agendamentos.keys()], default=0) + 1)
    
    agendamentos[novo_id] = {
        "id": novo_id,
        "servico_id": servico_id,
        "nome_servico": servico["nome"],
        "valor": servico["valor"],
        "comissao_percentual": servico["comissao_percentual"],
        "data_agendamento": data_hora,
        "cliente_id": cliente_id,
        "nome_cliente": cliente.get("nome", "Cliente"),
        "funcionario_id": funcionario_id,
        "status": "agendado"
    }
    return jsonify({"success": True, "agendamento": agendamentos[novo_id]})

@app.route('/api/agendamentos/<id>/concluir', methods=['PATCH'])
def api_concluir_agendamento(id):
    if id in agendamentos:
        agendamentos[id]["status"] = "concluido"
        return jsonify({"success": True, "agendamento": agendamentos[id]})
    return jsonify({"success": False, "message": "Agendamento não encontrado."}), 404

@app.route('/api/agendamentos/<id>/cancelar', methods=['PATCH'])
def api_cancelar_agendamento(id):
    if id in agendamentos:
        agendamentos[id]["status"] = "cancelado"
        return jsonify({"success": True, "agendamento": agendamentos[id]})
    return jsonify({"success": False, "message": "Agendamento não encontrado."}), 404

@app.route('/api/agendamentos/<id>', methods=['DELETE'])
def api_apagar_agendamento(id):
    if id in agendamentos:
        del agendamentos[id]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Agendamento não encontrado."}), 404


# === RELATÓRIOS ===
@app.route('/api/relatorios/financeiro')
def api_relatorio_financeiro():
    concluidos = [a for a in agendamentos.values() if a["status"] == "concluido"]
    
    faturamento = sum(a["valor"] for a in concluidos)
    comissoes = sum(a["valor"] * (a["comissao_percentual"] / 100.0) for a in concluidos)
    lucro = faturamento - comissoes
    
    return jsonify({
        "faturamento_bruto": round(faturamento, 2),
        "total_comissoes": round(comissoes, 2),
        "lucro_liquido": round(lucro, 2),
        "total_agendamentos_concluidos": len(concluidos)
    })

@app.route('/api/relatorios/funcionario/<int:func_id>')
def api_relatorio_funcionario(func_id):
    email_func = next((e for e, u in usuarios.items() if u["id"] == func_id and u["tipo_conta"] == "funcionario"), None)
    if not email_func:
        return jsonify({"success": False, "message": "Funcionário não encontrado."}), 404
        
    nome_funcionario = usuarios[email_func]["nome"]

    atendimentos = [
        a for a in agendamentos.values() 
        if a["funcionario_id"] == func_id and a["status"] == "concluido"
    ]
    
    total_comissao = sum(a["valor"] * (a["comissao_percentual"] / 100.0) for a in atendimentos)
    
    return jsonify({
        "funcionario_id": func_id,
        "nome_funcionario": nome_funcionario,
        "total_comissao_gerada": round(total_comissao, 2),
        "total_atendimentos_concluidos": len(atendimentos)
    })

# === CONTAS (Gerenciamento de Usuários) ===
@app.route('/api/contas', methods=['GET', 'POST'])
def api_contas():
    if request.method == 'GET':
        lista_contas = []
        for email, data in usuarios.items():
            lista_contas.append({
                "id": data["id"],
                "nome": data["nome"],
                "email": email,
                "tipo_conta": data["tipo_conta"]
            })
        return jsonify(lista_contas)
        
    return api_cadastrar()

@app.route('/api/contas/<int:id>', methods=['DELETE'])
def api_apagar_conta(id):
    email_para_apagar = next((e for e, u in usuarios.items() if u["id"] == id), None)

    if not email_para_apagar:
        return jsonify({"success": False, "message": "Usuário não encontrado."}), 404

    if usuarios[email_para_apagar]["tipo_conta"] == "gerente":
        num_gerentes = len([u for u in usuarios.values() if u["tipo_conta"] == "gerente"])
        if num_gerentes <= 1:
            return jsonify({"success": False, "message": "Não é possível apagar o único gerente do sistema."}), 403

    del usuarios[email_para_apagar]
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)


