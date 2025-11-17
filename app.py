from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, template_folder='templates')

# TOKEN PARA CRIAR NOVO GERENTE (mude se quiser)
GERENTE_TOKEN = "leonardo123"

# === DADOS DE DEMO ===
usuarios = {
    "gerente@salao.com": {
        "id": 1,
        "nome": "Leonardo Almeida",
        "senha": "demo123",
        "tipo_conta": "gerente"
    },
    "maria@salao.com": {
        "id": 2,
        "nome": "Maria Silva",
        "senha": "123",
        "tipo_conta": "funcionario"
    },
    "joao@salao.com": {
        "id": 3,
        "nome": "João Costa",
        "senha": "123",
        "tipo_conta": "funcionario"
    }
}

servicos = {
    "1": {"nome": "Corte Masculino", "valor": 60.0, "comissao_percentual": 35},
    "2": {"nome": "Barba", "valor": 40.0, "comissao_percentual": 40},
    "3": {"nome": "Corte + Barba", "valor": 90.0, "comissao_percentual": 38}
}

agendamentos = {
    "1": {"id": "1", "servico_id": "1", "valor": 60, "comissao_percentual": 35, "nome_cliente": "Pedro", "funcionario_id": 2, "status": "concluido"},
    "2": {"id": "2", "servico_id": "3", "valor": 90, "comissao_percentual": 38, "nome_cliente": "Ana", "funcionario_id": 2, "status": "concluido"},
    "3": {"id": "3", "servico_id": "2", "valor": 40, "comissao_percentual": 40, "nome_cliente": "Lucas", "funcionario_id": 3, "status": "concluido"}
}

# === ROTAS ===
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

# LOGIN DEMO
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    senha = data.get('senha')

    if email == "gerente@salao.com" and senha == "demo123":
        return jsonify({
            "success": True,
            "user": {"id": 1, "nome": "Leonardo Almeida", "tipo_conta": "gerente"}
        })
    return jsonify({"success": False, "message": "Use gerente@salao.com / demo123"})

# SERVIÇOS
@app.route('/api/servicos', methods=['GET', 'POST'])
def servicos_route():
    if request.method == 'GET':
        return jsonify(servicos)
    data = request.get_json()
    novo_id = str(max([int(k) for k in servicos.keys()], default=0) + 1)
    servicos[novo_id] = {
        "nome": data["nome"],
        "valor": float(data["valor"]),
        "comissao_percentual": int(data["comissao_percentual"])
    }
    return jsonify({"success": True})

@app.route('/api/servicos/<id>', methods=['DELETE'])
def delete_servico(id):
    if id in servicos:
        del servicos[id]
        return jsonify({"success": True})
    return jsonify({"success": False})

# FUNCIONÁRIOS + COMISSÃO
@app.route('/api/funcionarios', methods=['GET'])
def get_funcionarios():
    funcionarios = [u for u in usuarios.values() if u["tipo_conta"] == "funcionario"]
    
    comissoes = {}
    for func in funcionarios:
        atendimentos = [a for a in agendamentos.values() if a["funcionario_id"] == func["id"] and a["status"] == "concluido"]
        total = sum(a["valor"] * a["comissao_percentual"] / 100 for a in atendimentos)
        comissoes[func["id"]] = round(total, 2)
    
    return jsonify({
        "funcionarios": funcionarios,
        "comissoes": comissoes
    })

# CRIAR FUNCIONÁRIO OU GERENTE
@app.route('/api/criar-conta', methods=['POST'])
def criar_conta():
    data = request.get_json()
    email = data["email"]
    nome = data["nome"]
    senha = data["senha"]
    tipo = data["tipo"]
    token = data.get("token", "")

    if email in usuarios:
        return jsonify({"success": False, "message": "E-mail já existe"})

    if tipo == "gerente" and token != GERENTE_TOKEN:
        return jsonify({"success": False, "message": "Token inválido"})

    novo_id = max([u["id"] for u in usuarios.values()]) + 1
    usuarios[email] = {
        "id": novo_id,
        "nome": nome,
        "senha": senha,
        "tipo_conta": tipo
    }
    return jsonify({"success": True, "message": "Conta criada com sucesso!"})

# RELATÓRIO GERAL
@app.route('/api/relatorio')
def relatorio():
    concluidos = [a for a in agendamentos.values() if a["status"] == "concluido"]
    faturamento = sum(a["valor"] for a in concluidos)
    comissoes = sum(a["valor"] * a["comissao_percentual"] / 100 for a in concluidos)
    return jsonify({
        "faturamento": round(faturamento, 2),
        "comissoes": round(comissoes, 2),
        "lucro": round(faturamento - comissoes, 2)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)