from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, template_folder='templates')

# Token para criar novo gerente
GERENTE_TOKEN = "leonardo123"

# === DADOS DE DEMO ===
usuarios = {
    "gerente@salao.com": {"id": 1, "nome": "Leonardo Almeida", "senha": "demo123", "tipo_conta": "gerente"},
    "maria@salao.com":   {"id": 2, "nome": "Maria Silva",     "senha": "123", "tipo_conta": "funcionario"},
    "joao@salao.com":    {"id": 3, "nome": "João Costa",      "senha": "123", "tipo_conta": "funcionario"}
}

servicos = {
    "1": {"nome": "Corte Masculino",   "valor": 60.0, "comissao_percentual": 35},
    "2": {"nome": "Barba",             "valor": 40.0, "comissao_percentual": 40},
    "3": {"nome": "Corte + Barba",     "valor": 90.0, "comissao_percentual": 38}
}

agendamentos = {
    "1": {"id": "1", "servico_id": "1", "nome_servico": "Corte Masculino", "valor": 60, "comissao_percentual": 35,
          "data_hora": "2025-11-18 10:00", "nome_cliente": "Pedro Alves", "funcionario_id": 2, "status": "concluido"},
    "2": {"id": "2", "servico_id": "3", "nome_servico": "Corte + Barba", "valor": 90, "comissao_percentual": 38,
          "data_hora": "2025-11-18 14:30", "nome_cliente": "Lucas Mendes", "funcionario_id": 2, "status": "concluido"},
    "3": {"id": "3", "servico_id": "2", "nome_servico": "Barba", "valor": 40, "comissao_percentual": 40,
          "data_hora": "2025-11-19 16:00", "nome_cliente": "Ana Clara", "funcionario_id": 3, "status": "agendado"}
}

# === ROTAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('email') == "gerente@salao.com" and data.get('senha') == "demo123":
        return jsonify({"success": True, "user": {"id": 1, "nome": "Leonardo Almeida", "tipo_conta": "gerente"}})
    return jsonify({"success": False})

# SERVIÇOS
@app.route('/api/servicos', methods=['GET', 'POST'])
def servicos_route():
    if request.method == 'GET':
        return jsonify(servicos)
    data = request.get_json()
    novo_id = str(max(map(int, servicos.keys() or [0])) + 1)
    servicos[novo_id] = {"nome": data["nome"], "valor": float(data["valor"]), "comissao_percentual": int(data["comissao_percentual"])}
    return jsonify({"success": True})

@app.route('/api/servicos/<id>', methods=['DELETE'])
def delete_servico(id):
    servicos.pop(id, None)
    return jsonify({"success": True})

# FUNCIONÁRIOS
@app.route('/api/funcionarios', methods=['GET'])
def get_funcionarios():
    funcs = [u for u in usuarios.values() if u["tipo_conta"] == "funcionario"]
    comissoes = {}
    for f in funcs:
        total = sum(a["valor"] * a["comissao_percentual"] / 100 
                   for a in agendamentos.values() 
                   if a["funcionario_id"] == f["id"] and a["status"] == "concluido")
        comissoes[f["id"]] = round(total, 2)
    return jsonify({"funcionarios": funcs, "comissoes": comissoes})

@app.route('/api/funcionarios/<int:func_id>', methods=['DELETE'])
def delete_funcionario(func_id):
    email_to_delete = next((e for e, u in usuarios.items() if u["id"] == func_id), None)
    if email_to_delete and usuarios[email_to_delete]["tipo_conta"] == "funcionario":
        del usuarios[email_to_delete]
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Não encontrado ou não é funcionário"})

# CRIAR CONTA
@app.route('/api/criar-conta', methods=['POST'])
def criar_conta():
    data = request.get_json()
    if data["email"] in usuarios:
        return jsonify({"success": False, "message": "E-mail já existe"})
    if data["tipo"] == "gerente" and data.get("token") != GERENTE_TOKEN:
        return jsonify({"success": False, "message": "Token inválido"})
    
    novo_id = max(u["id"] for u in usuarios.values()) + 1
    usuarios[data["email"]] = {
        "id": novo_id, "nome": data["nome"], "senha": data["senha"], "tipo_conta": data["tipo"]
    }
    return jsonify({"success": True})

# AGENDAMENTOS
@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos():
    return jsonify(agendamentos)

@app.route('/api/agendamentos/<id>/concluir', methods=['PATCH'])
def concluir_agendamento(id):
    if id in agendamentos:
        agendamentos[id]["status"] = "concluido"
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route('/api/agendamentos/<id>', methods=['DELETE'])
def delete_agendamento(id):
    agendamentos.pop(id, None)
    return jsonify({"success": True})

# RELATÓRIO
@app.route('/api/relatorio')
def relatorio():
    concluidos = [a for a in agendamentos.values() if a["status"] == "concluido"]
    fat = sum(a["valor"] for a in concluidos)
    com = sum(a["valor"] * a["comissao_percentual"] / 100 for a in concluidos)
    return jsonify({"faturamento": round(fat, 2), "comissoes": round(com, 2), "lucro": round(fat - com, 2)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)