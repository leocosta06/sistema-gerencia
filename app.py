from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, template_folder='templates')

# === DADOS DE DEMO (APENAS GERENTE) ===
usuarios = {
    "gerente@salao.com": {
        "id": 1,
        "nome": "Leonardo Almeida",
        "senha": "demo123",
        "tipo_conta": "gerente"
    }
}

servicos = {
    "1": {"nome": "Corte Masculino", "valor": 60.0, "comissao_percentual": 35},
    "2": {"nome": "Barba Completa", "valor": 40.0, "comissao_percentual": 40},
    "3": {"nome": "Corte + Barba", "valor": 90.0, "comissao_percentual": 38},
    "4": {"nome": "Hidratação Capilar", "valor": 80.0, "comissao_percentual": 30}
}

agendamentos = {
    "1": {"id": "1", "servico_id": "1", "nome_servico": "Corte Masculino", "valor": 60, "comissao_percentual": 35,
          "data_agendamento": "2025-11-18 10:00", "nome_cliente": "Carlos Silva", "funcionario_id": 2, "status": "concluido"},
    "2": {"id": "2", "servico_id": "3", "nome_servico": "Corte + Barba", "valor": 90, "comissao_percentual": 38,
          "data_agendamento": "2025-11-18 14:30", "nome_cliente": "Pedro Costa", "funcionario_id": 2, "status": "concluido"},
    "3": {"id": "3", "servico_id": "1", "nome_servico": "Corte Masculino", "valor": 60, "comissao_percentual": 35,
          "data_agendamento": "2025-11-19 09:00", "nome_cliente": "Ana Lima", "funcionario_id": 2, "status": "agendado"}
}

# === ROTAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

# === LOGIN (DEMO = APENAS GERENTE) ===
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    # DEMO GERENTE
    if email == "gerente@salao.com" and senha == "demo123":
        return jsonify({
            "success": True,
            "user": {"id": 1, "nome": "Leonardo Almeida", "tipo_conta": "gerente"},
            "demo": True
        })

    return jsonify({"success": False, "message": "Credenciais inválidas no modo demo."})

# === SERVIÇOS ===
@app.route('/api/servicos', methods=['GET'])
def get_servicos():
    return jsonify(servicos)

@app.route('/api/servicos', methods=['POST'])
def add_servico():
    data = request.get_json()
    novo_id = str(max([int(k) for k in servicos.keys()], default=0) + 1)
    servicos[novo_id] = {
        "nome": data["nome"],
        "valor": float(data["valor"]),
        "comissao_percentual": int(data["comissao_percentual"])
    }
    return jsonify({"success": True, "id": novo_id})

@app.route('/api/servicos/<id>', methods=['DELETE'])
def del_servico(id):
    if id in servicos:
        del servicos[id]
        return jsonify({"success": True})
    return jsonify({"success": False})

# === AGENDAMENTOS ===
@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos():
    return jsonify(agendamentos)

@app.route('/api/agendamentos/<id>/concluir', methods=['PATCH'])
def concluir(id):
    if id in agendamentos:
        agendamentos[id]["status"] = "concluido"
        return jsonify({"success": True})
    return jsonify({"success": False})

# === RELATÓRIO FINANCEIRO ===
@app.route('/api/relatorios/financeiro')
def relatorio():
    concluidos = [a for a in agendamentos.values() if a["status"] == "concluido"]
    faturamento = sum(a["valor"] for a in concluidos)
    comissoes = sum(a["valor"] * a["comissao_percentual"] / 100 for a in concluidos)
    lucro = faturamento - comissoes
    return jsonify({
        "faturamento": round(faturamento, 2),
        "comissoes": round(comissoes, 2),
        "lucro": round(lucro, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)