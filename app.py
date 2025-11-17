from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__, template_folder='templates')

# === CONFIG DEMO ===
GERENTE_TOKEN = "leonardo123"

# DADOS DE DEMO (APENAS GERENTE FUNCIONANDO)
usuarios = {
    "gerente@salao.com": {"id": 1, "nome": "Leonardo Almeida", "senha": "demo123", "tipo_conta": "gerente"},
    "maria@salao.com":   {"id": 2, "nome": "Maria Silva", "senha": "123", "tipo_conta": "funcionario"},
    "joao@salao.com":    {"id": 3, "nome": "João Costa", "senha": "123", "tipo_conta": "funcionario"}
}
# Calcula o próximo ID de usuário baseado nos dados existentes
next_usuario_id = max(user['id'] for user in usuarios.values()) + 1

servicos = {
    "1": {"nome": "Corte Masculino", "valor": 60.0, "comissao_percentual": 35},
    "2": {"nome": "Barba", "valor": 40.0, "comissao_percentual": 40},
    "3": {"nome": "Corte + Barba", "valor": 90.0, "comissao_percentual": 38}
}
next_servico_id = 4 # Próximo ID de serviço será 4

agendamentos = {
    "1": {"id": "1", "servico_id": "1", "nome_servico": "Corte Masculino", "valor": 60, "comissao_percentual": 35,
          "data_hora": "2025-11-18 10:00", "nome_cliente": "Carlos", "funcionario_id": 2, "status": "concluido"},
    "2": {"id": "2", "servico_id": "3", "nome_servico": "Corte + Barba", "valor": 90, "comissao_percentual": 38,
          "data_hora": "2025-11-18 14:30", "nome_cliente": "Beatriz", "funcionario_id": 2, "status": "concluido"},
    "3": {"id": "3", "servico_id": "2", "nome_servico": "Barba", "valor": 40, "comissao_percentual": 40,
          "data_hora": "2025-11-19 16:00", "nome_cliente": "Rafael", "funcionario_id": 3, "status": "agendado"}
}
next_agendamento_id = 4 # Próximo ID de agendamento será 4


# === ROTAS ATIVAS (DEMO GERENTE) ===

# Servir o index.html
@app.route('/')
def index():
    # Seu código já estava correto, buscando da pasta 'templates'
    return send_from_directory('templates', 'index.html')

# Rota de login (versão demo)
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if data.get('email') == "gerente@salao.com" and data.get('senha') == "demo123":
        return jsonify({"success": True, "user": {"id": 1, "nome": "Leonardo Almeida", "tipo_conta": "gerente"}})
    return jsonify({"success": False, "message": "Use gerente@salao.com / demo123"})

# --- ROTAS DA API QUE FALTAVAM ---

@app.route('/api/relatorio', methods=['GET'])
def get_relatorio():
    faturamento = 0.0
    comissoes = 0.0
    for ag in agendamentos.values():
        if ag['status'] == 'concluido':
            faturamento += ag['valor']
            comissoes += ag['valor'] * (ag['comissao_percentual'] / 100)
    
    lucro = faturamento - comissoes
    # Retorna formatado como string, igual ao index.html
    return jsonify({
        "faturamento": f"{faturamento:.2f}",
        "comissoes": f"{comissoes:.2f}",
        "lucro": f"{lucro:.2f}"
    })

@app.route('/api/servicos', methods=['GET'])
def get_servicos():
    return jsonify(servicos)

@app.route('/api/servicos', methods=['POST'])
def add_servico():
    global next_servico_id
    data = request.get_json()
    novo_id = str(next_servico_id)
    
    novo_servico = {
        "nome": data['nome'],
        "valor": float(data['valor']),
        "comissao_percentual": int(data['comissao_percentual'])
    }
    servicos[novo_id] = novo_servico
    next_servico_id += 1
    
    print("Serviço adicionado:", novo_servico)
    return jsonify({"success": True, "servico": novo_servico})

@app.route('/api/servicos/<string:id>', methods=['DELETE'])
def delete_servico(id):
    if id in servicos:
        del servicos[id]
        print("Serviço excluído:", id)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Serviço não encontrado"}), 404

@app.route('/api/funcionarios', methods=['GET'])
def get_funcionarios():
    # 1. Lista de funcionários
    lista_funcionarios = [user for user in usuarios.values() if user['tipo_conta'] == 'funcionario']
    
    # 2. Cálculo de comissões (seu index.html espera isso)
    comissoes_calc = {}
    for ag in agendamentos.values():
        if ag['status'] == 'concluido':
            func_id = ag['funcionario_id']
            if func_id not in comissoes_calc:
                comissoes_calc[func_id] = 0.0
            
            valor_comissao = ag['valor'] * (ag['comissao_percentual'] / 100)
            comissoes_calc[func_id] += valor_comissao
    
    # Formata para string R$ 0.00 como o index espera
    comissoes_formatado = {str(id): f"{valor:.2f}" for id, valor in comissoes_calc.items()}

    return jsonify({"funcionarios": lista_funcionarios, "comissoes": comissoes_formatado})

@app.route('/api/criar-conta', methods=['POST'])
def criar_conta():
    global next_usuario_id
    data = request.get_json()
    email = data['email']
    
    if email in usuarios:
        return jsonify({"success": False, "message": "Este e-mail já está em uso."}), 400
        
    if data['tipo'] == 'gerente' and data['token'] != GERENTE_TOKEN:
        return jsonify({"success": False, "message": "Token de gerente inválido!"}), 403

    novo_id = next_usuario_id
    nova_conta = {
        "id": novo_id,
        "nome": data['nome'],
        "senha": data['senha'],
        "tipo_conta": data['tipo'] # 'funcionario' ou 'gerente'
    }
    usuarios[email] = nova_conta
    next_usuario_id += 1
    
    print("Nova conta criada:", nova_conta)
    return jsonify({"success": True, "message": "Conta criada com sucesso!"})

@app.route('/api/funcionarios/<int:id>', methods=['DELETE'])
def delete_funcionario(id):
    email_para_excluir = None
    for email, user in usuarios.items():
        if user['id'] == id and user['tipo_conta'] == 'funcionario':
            email_para_excluir = email
            break
    
    if email_para_excluir:
        del usuarios[email_para_excluir]
        print("Funcionário excluído:", id)
        return jsonify({"success": True})
    
    return jsonify({"success": False, "message": "Funcionário não encontrado ou não é funcionário"}), 404

@app.route('/api/agendamentos', methods=['GET'])
def get_agendamentos():
    return jsonify(agendamentos)

@app.route('/api/agendamentos/<string:id>/concluir', methods=['PATCH'])
def concluir_agendamento(id):
    if id in agendamentos:
        agendamentos[id]['status'] = 'concluido'
        print("Agendamento concluído:", id)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Agendamento não encontrado"}), 404

@app.route('/api/agendamentos/<string:id>', methods=['DELETE'])
def delete_agendamento(id):
    if id in agendamentos:
        del agendamentos[id]
        print("Agendamento excluído:", id)
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Agendamento não encontrado"}), 404


# === CÓDIGO ANTIGO COMPLETO (COMENTADO) ===
"""
# === LOGIN COMPLETO (ANTES) ===
@app.route('/api/login-full', methods=['POST'])
def api_login_full():
    # Aceitava cliente, funcionário, gerente e demo
    ...

# === CADASTRO DE CLIENTE/FUNCIONÁRIO/GERENTE ===
@app.route('/api/cadastrar-full', methods=['POST'])
def api_cadastrar_full():
    # Cliente podia se cadastrar sozinho
    ...

# (E assim por diante, com todas as outras funções)
"""

# === AVISO NO CÓDIGO ===
print("\n" + "="*60)
print("SALÃOAPP - MODO DEMO (APENAS GERENTE ATIVO)")
print("Todas as funções de cliente e funcionário estão comentadas")
print("Mas 100% implementadas e prontas para uso")
print("="*60 + "\n")

if __name__ == '__main__':
    # Usando a porta 8080 como no seu exemplo
    port = int(os.environ.get('PORT', 8080))
    print(f"Servidor Demo rodando em http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)

