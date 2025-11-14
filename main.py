import streamlit as st
import backend_logic # Importa o nome de ficheiro correto
import pandas as pd
from datetime import time, datetime

# Configuração da página
st.set_page_config(
    page_title="Sistema do Salão",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Funções Auxiliares da Interface ---

def inicializar_firebase():
    if "firebase_iniciado" not in st.session_state:
        # Chama a função de inicialização (que agora lê o secret)
        sucesso, mensagem = backend_logic.inicializar_firebase()
        if sucesso:
            st.session_state.firebase_iniciado = True
        else:
            # Mostra o erro exato que veio do backend
            st.error(f"❌ ERRO: {mensagem}")
            st.stop()
            
def fazer_logout():
    chaves_para_limpar = ["utilizador_logado", "dados_utilizador", "pagina_atual", "item_em_edicao"]
    for chave in chaves_para_limpar:
        if chave in st.session_state:
            del st.session_state[chave]
    st.rerun()

# --- TELAS PRINCIPAIS (Login, Setup e Menus) ---

def tela_login():
    st.title("🏪 Sistema de Gestão do Salão")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 Fazer Login")
        with st.form("form_login"):
            email = st.text_input("📧 E-mail:", placeholder="Digite seu e-mail")
            senha = st.text_input("🔑 Senha:", type="password", placeholder="Digite sua senha")
            
            if st.form_submit_button("🚀 Entrar", use_container_width=True):
                if email and senha:
                    resultado, erro = backend_logic.verificar_login(email, senha)
                    if resultado:
                        st.session_state.utilizador_logado, st.session_state.dados_utilizador = resultado
                        st.rerun()
                    else:
                        st.error(f"❌ {erro}")
                else:
                    st.warning("⚠️ Por favor, preencha todos os campos!")

def tela_setup_inicial():
    """Mostra esta tela se nenhum gerente for encontrado no banco de dados."""
    st.title("🏪 Bem-vindo ao Sistema de Gestão do Salão")
    st.header("🚀 Configuração Inicial")
    st.warning("Nenhuma conta de gerente foi encontrada. Por favor, crie a primeira conta de administrador.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("form_setup_gerente"):
            st.subheader("Registar o Primeiro Gerente")
            nome = st.text_input("Nome completo")
            email = st.text_input("E-mail (será o seu login)")
            senha = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Criar Conta de Gerente", use_container_width=True):
                if nome and email and senha:
                    sucesso, msg = backend_logic.registrar_usuario(nome, email, senha, 'gerente')
                    if sucesso:
                        st.success(msg)
                        st.info("A aplicação será recarregada. Por favor, faça login com as suas novas credenciais.")
                        st.session_state.clear() 
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Por favor, preencha todos os campos.")

def menu_gerente():
    nome = st.session_state.dados_utilizador.get('nome', 'Gerente')
    with st.sidebar:
        st.success(f"👨‍💼 Logado como: **{nome}**")
        st.info("🏢 **Tipo**: Gerente")
        if st.button("🚪 Logout", use_container_width=True):
            fazer_logout()

    st.title("👨‍💼 Painel do Gerente")

    paginas = {
        "Menu Principal": pagina_menu_principal_gerente,
        "Gerir Agenda": pagina_gerir_agenda,
        "Gerir Clientes": pagina_gerir_clientes,
        "Gerir Funcionários": pagina_gerir_funcionarios,
        "Gerir Gerentes": pagina_gerir_gerentes,
        "Gerir Serviços": pagina_gerir_servicos,
        "Ver Relatórios": pagina_ver_relatorios_gerente,
        "Analisar Frequência": pagina_analisar_frequencia,
        "Ver Comissão de Funcionário": pagina_ver_comissao_funcionario,
    }
    
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = "Menu Principal"
        
    pagina_selecionada = st.session_state.pagina_atual
    paginas[pagina_selecionada]()

def menu_cliente():
    nome = st.session_state.dados_utilizador.get('nome', 'Cliente')
    with st.sidebar:
        st.success(f"👤 Logado como: **{nome}**")
        st.info("🙋 **Tipo**: Cliente")
        if st.button("🚪 Logout", use_container_width=True):
            fazer_logout()
    
    st.title("👤 Portal do Cliente")
    paginas = {
        "Menu Principal": pagina_menu_principal_cliente,
        "Marcar Agendamento": pagina_marcar_agendamento,
        "Meus Agendamentos": pagina_ver_meus_agendamentos,
    }
    if 'pagina_atual' not in st.session_state: st.session_state.pagina_atual = "Menu Principal"
    paginas[st.session_state.pagina_atual]()
    
def menu_funcionario():
    nome = st.session_state.dados_utilizador.get('nome', 'Funcionário')
    with st.sidebar:
        st.success(f"👩‍🔧 Logado como: **{nome}**")
        st.info("⚒️ **Tipo**: Funcionário")
        if st.button("🚪 Logout", use_container_width=True):
            fazer_logout()
    
    st.title("👩‍🔧 Portal do Funcionário")
    pagina_ver_relatorio_funcionario()

# --- PÁGINAS DE MENU ---

def pagina_menu_principal_gerente():
    st.markdown("---")
    st.subheader("Selecione uma opção para começar:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📅 Gerir Agenda", on_click=lambda: st.session_state.update(pagina_atual="Gerir Agenda"), use_container_width=True)
        st.button("👤 Gerir Clientes", on_click=lambda: st.session_state.update(pagina_atual="Gerir Clientes"), use_container_width=True)
    with col2:
        st.button("👥 Gerir Funcionários", on_click=lambda: st.session_state.update(pagina_atual="Gerir Funcionários"), use_container_width=True)
        st.button("👑 Gerir Gerentes", on_click=lambda: st.session_state.update(pagina_atual="Gerir Gerentes"), use_container_width=True)
        st.button("💇 Gerir Serviços", on_click=lambda: st.session_state.update(pagina_atual="Gerir Serviços"), use_container_width=True)
    with col3:
        st.button("📈 Ver Relatórios", on_click=lambda: st.session_state.update(pagina_atual="Ver Relatórios"), use_container_width=True)
        st.button("🧐 Analisar Frequência", on_click=lambda: st.session_state.update(pagina_atual="Analisar Frequência"), use_container_width=True)
        st.button("💰 Ver Comissão de Funcionário", on_click=lambda: st.session_state.update(pagina_atual="Ver Comissão de Funcionário"), use_container_width=True)

def pagina_menu_principal_cliente():
    st.markdown("---")
    st.subheader("O que você gostaria de fazer?")
    if st.button("➕ Marcar um Novo Agendamento", use_container_width=True):
        st.session_state.pagina_atual = "Marcar Agendamento"; st.rerun()
    if st.button("📅 Ver Meus Agendamentos", use_container_width=True):
        st.session_state.pagina_atual = "Meus Agendamentos"; st.rerun()

# --- PÁGINAS DE FUNCIONALIDADES (GERENTE) ---

def pagina_gerir_clientes():
    st.header("👤 Gestão de Clientes")

    if 'item_em_edicao' in st.session_state and st.session_state.item_em_edicao[1].get('tipo_conta') == 'cliente':
        id_cliente_edicao, dados_cliente = st.session_state.item_em_edicao
        st.subheader(f"✏️ Editando Cliente: {dados_cliente['nome']}")
        with st.form("form_edit_cliente"):
            novo_nome = st.text_input("Nome", value=dados_cliente['nome'])
            novo_telefone = st.text_input("Telefone", value=dados_cliente['telefone'])
            novo_email = st.text_input("E-mail", value=dados_cliente['email'])
            
            col1, col2 = st.columns(2)
            if col1.form_submit_button("Salvar Alterações"):
                novos_dados = {'nome': novo_nome, 'telefone': novo_telefone, 'email': novo_email}
                sucesso, msg = backend_logic.editar_dados('contas', id_cliente_edicao, novos_dados)
                if sucesso: st.success(msg)
                else: st.error(msg)
                del st.session_state.item_em_edicao
                st.rerun()
            if col2.form_submit_button("Cancelar", type="secondary"):
                del st.session_state.item_em_edicao
                st.rerun()
    else:
        with st.expander("➕ Adicionar Novo Cliente"):
            with st.form("form_novo_cliente", clear_on_submit=True):
                nome = st.text_input("Nome completo"); telefone = st.text_input("Telefone")
                email = st.text_input("E-mail (login)"); senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Salvar Cliente"):
                    sucesso, msg = backend_logic.registrar_cliente(nome, telefone, email, senha)
                    if sucesso: st.success(msg)
                    else: st.error(msg)

    st.markdown("---")
    st.subheader("📋 Lista de Clientes")
    clientes, erro = backend_logic.listar_dados('clientes')
    if erro: st.error(erro)
    elif not clientes: st.info("Nenhum cliente registado.")
    else:
        for id_cliente, dados in clientes.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{dados['nome']}** ({dados['email']})")
            if col2.button("✏️ Editar", key=f"edit_{id_cliente}"):
                st.session_state.item_em_edicao = (id_cliente, dados)
                st.rerun()
            if col3.button("❌ Remover", key=f"del_{id_cliente}"):
                sucesso, msg = backend_logic.remover_usuario(id_cliente)
                if sucesso: st.success(msg)
                else: st.error(msg)
                st.rerun()

    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()


def pagina_gerir_agenda():
    st.header("📅 Gestão da Agenda")
    agendamentos, erro = backend_logic.listar_dados('agendamentos')
    if erro: st.error(erro); return
    pendentes = {id_ag: ag for id_ag, ag in agendamentos.items() if ag.get('status') == 'agendado'}
    
    st.subheader("🗓️ Agendamentos Pendentes")
    if not pendentes: st.info("Nenhum agendamento pendente.")
    else:
        for id_ag, ag in pendentes.items():
            with st.container(border=True):
                st.write(f"**Cliente:** {ag['nome_cliente']} | **Serviço:** {ag['nome_servico']} | **Data:** {ag['data_agendamento']}")
                col1, col2 = st.columns(2)
                if col1.button("✅ Concluir", key=f"concluir_{id_ag}", use_container_width=True):
                    sucesso, msg = backend_logic.atualizar_status_agendamento(id_ag, 'concluido'); 
                    if sucesso: st.success(msg) 
                    else: st.error(msg)
                    st.rerun()
                if col2.button("❌ Cancelar", key=f"cancelar_{id_ag}", use_container_width=True):
                    sucesso, msg = backend_logic.atualizar_status_agendamento(id_ag, 'cancelado'); 
                    if sucesso: st.warning(msg) 
                    else: st.error(msg)
                    st.rerun()
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_gerir_funcionarios():
    st.header("👥 Gestão de Funcionários")
    if 'item_em_edicao' in st.session_state and st.session_state.item_em_edicao[1].get('tipo_conta') == 'funcionario':
        id_func, dados_func = st.session_state.item_em_edicao
        st.subheader(f"✏️ Editando Funcionário: {dados_func['nome']}")
        with st.form("form_edit_func"):
            novo_nome = st.text_input("Nome", value=dados_func['nome'])
            novo_email = st.text_input("E-mail", value=dados_func['email'])
            col1, col2 = st.columns(2)
            if col1.form_submit_button("Salvar"):
                sucesso, msg = backend_logic.editar_dados('contas', id_func, {'nome': novo_nome, 'email': novo_email})
                if sucesso: st.success(msg)
                else: st.error(msg)
                del st.session_state.item_em_edicao; st.rerun()
            if col2.form_submit_button("Cancelar", type="secondary"):
                del st.session_state.item_em_edicao; st.rerun()
    else:
        with st.expander("➕ Adicionar Novo Funcionário"):
            with st.form("form_novo_func", clear_on_submit=True):
                nome = st.text_input("Nome"); email = st.text_input("E-mail")
                senha = st.text_input("Senha", type="password")
                if st.form_submit_button("Salvar"):
                    sucesso, msg = backend_logic.registrar_usuario(nome, email, senha, 'funcionario')
                    if sucesso: st.success(msg)
                    else: st.error(msg)
    
    st.markdown("---")
    st.subheader("📋 Lista de Funcionários")
    funcs, erro = backend_logic.listar_dados('funcionarios')
    if erro: st.error(erro)
    elif not funcs: st.info("Nenhum funcionário registado.")
    else:
        for id_func, dados in funcs.items():
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"**{dados['nome']}** ({dados['email']})")
            if col2.button("✏️ Editar", key=f"edit_func_{id_func}"):
                st.session_state.item_em_edicao = (id_func, dados); st.rerun()
            if col3.button("❌ Remover", key=f"del_func_{id_func}"):
                backend_logic.remover_usuario(id_func); st.rerun()
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_gerir_gerentes():
    st.header("👑 Gestão de Gerentes")
    with st.expander("➕ Adicionar Novo Gerente"):
        with st.form("form_novo_gerente", clear_on_submit=True):
            nome = st.text_input("Nome completo"); email = st.text_input("E-mail (login)")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Salvar Gerente"):
                sucesso, msg = backend_logic.registrar_usuario(nome, email, senha, 'gerente')
                if sucesso: st.success(msg)
                else: st.error(msg)
    st.markdown("---")
    st.subheader("📋 Lista de Gerentes")
    gerentes, erro = backend_logic.listar_dados('gerentes')
    if erro: st.error(erro)
    elif not gerentes: st.info("Nenhum gerente registado.")
    else:
        id_gerente_logado = st.session_state.utilizador_logado
        for id_gerente, dados_gerente in gerentes.items():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Nome:** {dados_gerente['nome']} | **Email:** {dados_gerente['email']}")
            with col2:
                if id_gerente != id_gerente_logado:
                    if st.button("Remover", key=f"remover_{id_gerente}", use_container_width=True):
                        sucesso, msg = backend_logic.remover_usuario(id_gerente)
                        if sucesso: st.success(msg); st.rerun()
                        else: st.error(msg)
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_gerir_servicos():
    st.header("💇 Gestão de Serviços")
    with st.expander("➕ Adicionar Novo Serviço"):
        with st.form("form_novo_serv", clear_on_submit=True):
            nome = st.text_input("Nome do Serviço")
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            comissao = st.number_input("Comissão (%)", min_value=0, max_value=100)
            if st.form_submit_button("Salvar Serviço"):
                sucesso, msg = backend_logic.adicionar_servico(nome, valor, comissao)
                if sucesso: st.success(msg)
                else: st.error(msg)
    st.markdown("---")
    st.subheader("📋 Catálogo de Serviços")
    servicos, erro = backend_logic.listar_dados('servicos')
    if erro: st.error(erro)
    elif not servicos: st.info("Nenhum serviço registado.")
    else: st.dataframe(pd.DataFrame.from_dict(servicos, orient='index'))
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_ver_relatorios_gerente():
    st.header("📈 Relatórios Gerenciais")
    relatorio, erro = backend_logic.gerar_relatorio_geral()
    if erro: st.error(erro)
    elif not relatorio['faturamento_total'] > 0: st.info("Não há dados de atendimentos para gerar relatórios.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {relatorio['faturamento_total']:.2f}")
        col2.metric("Total em Comissões", f"R$ {relatorio['total_comissoes']:.2f}")
        col3.metric("Lucro Bruto", f"R$ {relatorio['lucro_bruto']:.2f}")
        st.markdown("---")
        st.subheader("⭐ Serviços Mais Populares")
        df_populares = pd.DataFrame(relatorio['servicos_populares'], columns=['Serviço', 'Quantidade'])
        st.dataframe(df_populares)
        st.bar_chart(df_populares.set_index('Serviço'))
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_analisar_frequencia():
    st.header("🧐 Análise de Frequência de Cliente")
    clientes, erro = backend_logic.listar_dados('clientes')
    if erro: st.error(erro); return
    if not clientes: st.info("Nenhum cliente para analisar."); return
    opcoes_clientes = {dados['nome']: id_cliente for id_cliente, dados in clientes.items()}
    cliente_selecionado_nome = st.selectbox("Selecione um cliente para analisar:", options=opcoes_clientes.keys())
    if cliente_selecionado_nome:
        id_cliente_selecionado = opcoes_clientes[cliente_selecionado_nome]
        analise, erro_analise = backend_logic.analisar_frequencia_cliente(id_cliente_selecionado)
        if erro_analise: st.error(erro_analise)
        else:
            st.markdown("---")
            col1, col2 = st.columns(2)
            col1.metric("Total de Visitas", f"{analise['total_visitas']} atendimentos")
            col2.metric("Frequência Média", f"{analise['frequencia']:.2f} visitas/mês")
            st.info(f"Cliente desde: {analise['desde']}")
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_ver_comissao_funcionario():
    st.header("💰 Consultar Comissão de Funcionário")
    funcionarios, erro = backend_logic.listar_dados('funcionarios')
    if erro: st.error(erro); return
    if not funcionarios: st.info("Nenhum funcionário para consultar."); return
    opcoes_funcionarios = {dados['nome']: id_func for id_func, dados in funcionarios.items()}
    func_selecionado_nome = st.selectbox("Selecione um funcionário:", options=opcoes_funcionarios.keys())
    if func_selecionado_nome:
        id_func_selecionado = opcoes_funcionarios[func_selecionado_nome]
        relatorio, erro_rel = backend_logic.gerar_relatorio_individual(id_func_selecionado)
        if erro_rel: st.error(erro_rel)
        else:
            st.markdown("---")
            st.subheader(f"Desempenho de {func_selecionado_nome}")
            col1, col2 = st.columns(2)
            col1.metric("Total de Atendimentos", relatorio['total_atendimentos'])
            col2.metric("Comissão a Receber", f"R$ {relatorio['comissao_total']:.2f}")
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

# --- PÁGINAS DE FUNCIONALIDADES (CLIENTE E FUNCIONÁRIO) ---

def pagina_marcar_agendamento():
    st.header("➕ Marcar Novo Agendamento")
    servicos, erro_s = backend_logic.listar_dados('servicos')
    funcionarios, erro_f = backend_logic.listar_dados('funcionarios')
    if erro_s or erro_f: st.error(erro_s or erro_f); return
    if not servicos or not funcionarios: st.warning("Não há serviços ou funcionários disponíveis."); return
    opcoes_servicos = {s['nome']: id_s for id_s, s in servicos.items()}
    opcoes_funcionarios = {f['nome']: id_f for id_f, f in funcionarios.items()}
    with st.form("form_agendamento"):
        servico_nome = st.selectbox("Escolha o serviço:", options=opcoes_servicos.keys())
        func_nome = st.selectbox("Escolha o profissional:", options=opcoes_funcionarios.keys())
        data = st.date_input("Escolha a data:")
        hora = st.time_input("Escolha a hora:", value=time(9, 0)) # Corrigido: min_value/max_value removidos
        if st.form_submit_button("Confirmar Agendamento"):
            id_servico = opcoes_servicos[servico_nome]; id_funcionario = opcoes_funcionarios[func_nome]
            data_hora_str = f"{data} {hora.strftime('%H:%M')}"
            sucesso, msg = backend_logic.marcar_novo_agendamento(st.session_state.utilizador_logado, st.session_state.dados_utilizador, id_funcionario, id_servico, data_hora_str)
            if sucesso: st.success(msg)
            else: st.error(msg)
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_ver_meus_agendamentos():
    st.header("📅 Meus Agendamentos")
    agendamentos, erro = backend_logic.listar_dados('agendamentos')
    if erro: st.error(erro)
    else:
        meus_agendamentos = {id_ag: ag for id_ag, ag in agendamentos.items() if ag.get('id_cliente') == st.session_state.utilizador_logado}
        if not meus_agendamentos: st.info("Você ainda não possui agendamentos.")
        else:
            df_meus_ag = pd.DataFrame.from_dict(meus_agendamentos, orient='index')
            st.dataframe(df_meus_ag[['data_agendamento', 'nome_servico', 'nome_funcionario', 'status']])
    if st.button("⬅️ Voltar"): st.session_state.pagina_atual = "Menu Principal"; st.rerun()

def pagina_ver_relatorio_funcionario():
    st.header("💰 Meu Relatório de Comissões")
    relatorio, erro = backend_logic.gerar_relatorio_individual(st.session_state.utilizador_logado)
    if erro: st.error(erro)
    elif not relatorio or relatorio['total_atendimentos'] == 0:
        st.info("Você ainda não realizou atendimentos.")
    else:
        col1, col2 = st.columns(2)
        col1.metric("Total de Atendimentos", relatorio['total_atendimentos'])
        col2.metric("Comissão Total a Receber", f"R$ {relatorio['comissao_total']:.2f}")

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

def main():
    """Função principal que controla o fluxo da aplicação."""
    inicializar_firebase()
    
    # Verifica se há algum gerente registado
    gerentes, _ = backend_logic.listar_dados('gerentes')
    
    if "utilizador_logado" not in st.session_state:
        # Se não houver gerentes, força a tela de setup
        if not gerentes:
            tela_setup_inicial()
        else:
            tela_login()
    else:
        # Se está logado, mostra o menu apropriado
        tipo_conta = st.session_state.dados_utilizador.get('tipo_conta')
        if tipo_conta == 'gerente': menu_gerente()
        elif tipo_conta == 'cliente': menu_cliente()
        elif tipo_conta == 'funcionario': menu_funcionario()
        else:
            st.error("Tipo de conta não reconhecido.")
            if st.button("Sair"): fazer_logout()

if __name__ == '__main__':
    main()
