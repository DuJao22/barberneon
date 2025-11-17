from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
import database as db
import os
import secrets
import re

load_dotenv()

app = Flask(__name__)

if not os.getenv('SESSION_SECRET'):
    app.secret_key = secrets.token_hex(32)
else:
    app.secret_key = os.getenv('SESSION_SECRET')

app.config['TEMPLATES_AUTO_RELOAD'] = True

db.init_database()
db.popular_dados_exemplo()

def get_configuracoes():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM configuracoes')
    configs_raw = cursor.fetchall()
    conn.close()
    
    configs = {}
    for config in configs_raw:
        configs[config['chave']] = config['valor']
    
    return configs

@app.context_processor
def inject_configs():
    return dict(site_config=get_configuracoes())

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('login_admin'))
        return f(*args, **kwargs)
    return decorated_function

def cliente_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('cliente_id'):
            session['redirect_after_login'] = request.url
            flash('Você precisa fazer login para acessar esta página', 'error')
            return redirect(url_for('login_cliente'))
        return f(*args, **kwargs)
    return decorated_function

def validate_agendamento_data(data):
    required_fields = ['barbeiro_id', 'servico_id', 'data', 'horario']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Campo obrigatório ausente: {field}"
    
    try:
        barbeiro_id = int(data['barbeiro_id'])
        servico_id = int(data['servico_id'])
    except (ValueError, TypeError):
        return False, "IDs inválidos"
    
    try:
        datetime.strptime(data['data'], '%Y-%m-%d')
        datetime.strptime(data['horario'], '%H:%M')
    except ValueError:
        return False, "Formato de data/hora inválido"
    
    return True, None

@app.route('/landing')
def landing():
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    return render_template('landing.html', carrinho_count=carrinho_count)

@app.route('/')
def index():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM categorias WHERE ativo = 1 ORDER BY ordem')
    categorias = cursor.fetchall()
    
    cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                     LEFT JOIN categorias c ON s.categoria_id = c.id 
                     WHERE s.ativo = 1 AND s.destaque = 1''')
    servicos_destaque = cursor.fetchall()
    
    cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                     LEFT JOIN categorias c ON p.categoria_id = c.id 
                     WHERE p.ativo = 1 AND p.destaque = 1''')
    produtos_destaque = cursor.fetchall()
    
    cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                     LEFT JOIN categorias c ON s.categoria_id = c.id 
                     WHERE s.ativo = 1 AND s.promocao = 1''')
    servicos_promocao = cursor.fetchall()
    
    cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                     LEFT JOIN categorias c ON p.categoria_id = c.id 
                     WHERE p.ativo = 1 AND p.promocao = 1''')
    produtos_promocao = cursor.fetchall()
    
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'status_aberto'")
    config = cursor.fetchone()
    status_aberto = config['valor'] == '1' if config else True
    
    conn.close()
    
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('index.html', 
                          categorias=categorias,
                          servicos_destaque=servicos_destaque,
                          produtos_destaque=produtos_destaque,
                          servicos_promocao=servicos_promocao,
                          produtos_promocao=produtos_promocao,
                          status_aberto=status_aberto,
                          carrinho_count=carrinho_count)

@app.route('/categoria/<int:categoria_id>')
def categoria(categoria_id):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM categorias WHERE id = ?', (categoria_id,))
    categoria = cursor.fetchone()
    
    if categoria_id == 1:
        cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                         LEFT JOIN categorias c ON s.categoria_id = c.id 
                         WHERE s.ativo = 1 AND s.destaque = 1''')
        servicos = cursor.fetchall()
        
        cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                         LEFT JOIN categorias c ON p.categoria_id = c.id 
                         WHERE p.ativo = 1 AND p.destaque = 1''')
        produtos = cursor.fetchall()
    elif categoria_id == 2:
        cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                         LEFT JOIN categorias c ON s.categoria_id = c.id 
                         WHERE s.ativo = 1 AND s.promocao = 1''')
        servicos = cursor.fetchall()
        
        cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                         LEFT JOIN categorias c ON p.categoria_id = c.id 
                         WHERE p.ativo = 1 AND p.promocao = 1''')
        produtos = cursor.fetchall()
    else:
        cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                         LEFT JOIN categorias c ON s.categoria_id = c.id 
                         WHERE s.ativo = 1 AND s.categoria_id = ?''', (categoria_id,))
        servicos = cursor.fetchall()
        
        cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                         LEFT JOIN categorias c ON p.categoria_id = c.id 
                         WHERE p.ativo = 1 AND p.categoria_id = ?''', (categoria_id,))
        produtos = cursor.fetchall()
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('categoria.html', 
                          categoria=categoria,
                          servicos=servicos,
                          produtos=produtos,
                          carrinho_count=carrinho_count)

@app.route('/servico/<int:servico_id>')
def servico_detalhes(servico_id):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s 
                     LEFT JOIN categorias c ON s.categoria_id = c.id 
                     WHERE s.id = ?''', (servico_id,))
    servico = cursor.fetchone()
    
    cursor.execute('SELECT * FROM barbeiros WHERE ativo = 1')
    barbeiros = cursor.fetchall()
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('servico.html', 
                          servico=servico,
                          barbeiros=barbeiros,
                          carrinho_count=carrinho_count)

@app.route('/produto/<int:produto_id>')
def produto_detalhes(produto_id):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p 
                     LEFT JOIN categorias c ON p.categoria_id = c.id 
                     WHERE p.id = ?''', (produto_id,))
    produto = cursor.fetchone()
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('produto.html', 
                          produto=produto,
                          carrinho_count=carrinho_count)

@app.route('/buscar')
def buscar():
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('index'))
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    search_term = f'%{query}%'
    
    cursor.execute('''SELECT s.*, c.nome as categoria_nome, 'servico' as tipo FROM servicos s 
                     LEFT JOIN categorias c ON s.categoria_id = c.id 
                     WHERE s.ativo = 1 AND (s.nome LIKE ? OR s.descricao LIKE ?)''', 
                     (search_term, search_term))
    resultados = cursor.fetchall()
    
    cursor.execute('''SELECT p.*, c.nome as categoria_nome, 'produto' as tipo FROM produtos p 
                     LEFT JOIN categorias c ON p.categoria_id = c.id 
                     WHERE p.ativo = 1 AND (p.nome LIKE ? OR p.descricao LIKE ?)''', 
                     (search_term, search_term))
    resultados_produtos = cursor.fetchall()
    
    conn.close()
    
    todos_resultados = list(resultados) + list(resultados_produtos)
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('buscar.html', 
                          query=query,
                          resultados=todos_resultados,
                          carrinho_count=carrinho_count)

@app.route('/carrinho')
def carrinho():
    carrinho_items = session.get('carrinho', [])
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    itens_detalhados = []
    total = 0
    
    for item in carrinho_items:
        if item['tipo'] == 'servico':
            cursor.execute('SELECT * FROM servicos WHERE id = ?', (item['id'],))
            dados = cursor.fetchone()
            if dados:
                preco = dados['preco_promocional'] if dados['promocao'] and dados['preco_promocional'] else dados['preco']
                itens_detalhados.append({
                    'id': dados['id'],
                    'tipo': 'servico',
                    'nome': dados['nome'],
                    'preco': preco,
                    'quantidade': item.get('quantidade', 1),
                    'imagem': dados['imagem']
                })
                total += preco * item.get('quantidade', 1)
        else:
            cursor.execute('SELECT * FROM produtos WHERE id = ?', (item['id'],))
            dados = cursor.fetchone()
            if dados:
                preco = dados['preco_promocional'] if dados['promocao'] and dados['preco_promocional'] else dados['preco']
                itens_detalhados.append({
                    'id': dados['id'],
                    'tipo': 'produto',
                    'nome': dados['nome'],
                    'preco': preco,
                    'quantidade': item.get('quantidade', 1),
                    'imagem': dados['imagem']
                })
                total += preco * item.get('quantidade', 1)
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in carrinho_items)
    
    return render_template('carrinho.html', 
                          itens=itens_detalhados,
                          total=total,
                          carrinho_count=carrinho_count)

@app.route('/adicionar-carrinho', methods=['POST'])
def adicionar_carrinho():
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    tipo = data.get('tipo')
    item_id = data.get('id')
    quantidade = data.get('quantidade', 1)
    
    if tipo not in ['servico', 'produto']:
        return jsonify({'success': False, 'error': 'Tipo inválido'}), 400
    
    try:
        item_id = int(item_id)
        quantidade = int(quantidade)
        if quantidade <= 0 or quantidade > 100:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Quantidade inválida'}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    if tipo == 'servico':
        cursor.execute('SELECT id FROM servicos WHERE id = ? AND ativo = 1', (item_id,))
        item = cursor.fetchone()
    else:
        cursor.execute('SELECT id, estoque FROM produtos WHERE id = ? AND ativo = 1', (item_id,))
        item = cursor.fetchone()
        if item and item['estoque'] < quantidade:
            conn.close()
            return jsonify({'success': False, 'error': 'Estoque insuficiente'}), 400
    
    conn.close()
    
    if not item:
        return jsonify({'success': False, 'error': 'Item não encontrado'}), 404
    
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    carrinho = session['carrinho']
    
    item_existente = next((item for item in carrinho if item['tipo'] == tipo and item['id'] == item_id), None)
    
    if item_existente:
        item_existente['quantidade'] = item_existente.get('quantidade', 1) + quantidade
    else:
        carrinho.append({
            'tipo': tipo,
            'id': item_id,
            'quantidade': quantidade
        })
    
    session['carrinho'] = carrinho
    session.modified = True
    
    total_itens = sum(item.get('quantidade', 1) for item in carrinho)
    return jsonify({'success': True, 'count': total_itens, 'carrinho': carrinho})

@app.route('/remover-carrinho', methods=['POST'])
def remover_carrinho():
    data = request.get_json()
    tipo = data.get('tipo')
    item_id = data.get('id')
    
    if 'carrinho' in session:
        carrinho = session['carrinho']
        session['carrinho'] = [item for item in carrinho if not (item['tipo'] == tipo and item['id'] == item_id)]
        session.modified = True
    
    total_itens = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    return jsonify({'success': True, 'count': total_itens})

@app.route('/limpar-carrinho', methods=['POST'])
def limpar_carrinho():
    session['carrinho'] = []
    session.modified = True
    return jsonify({'success': True})

@app.route('/restaurar-carrinho', methods=['POST'])
def restaurar_carrinho():
    data = request.get_json()
    carrinho_local = data.get('carrinho', [])
    
    if not carrinho_local:
        return jsonify({'success': True})
    
    if 'carrinho' not in session:
        session['carrinho'] = []
    
    carrinho_sessao = session['carrinho']
    
    for item_local in carrinho_local:
        tipo = item_local.get('tipo')
        item_id = item_local.get('id')
        quantidade = item_local.get('quantidade', 1)
        
        item_existente = next((item for item in carrinho_sessao if item['tipo'] == tipo and item['id'] == item_id), None)
        
        if item_existente:
            item_existente['quantidade'] = item_existente.get('quantidade', 1) + quantidade
        else:
            carrinho_sessao.append({
                'tipo': tipo,
                'id': item_id,
                'quantidade': quantidade
            })
    
    session['carrinho'] = carrinho_sessao
    session.modified = True
    
    total_itens = sum(item.get('quantidade', 1) for item in carrinho_sessao)
    return jsonify({'success': True, 'count': total_itens})

@app.route('/alterar-quantidade-carrinho', methods=['POST'])
def alterar_quantidade_carrinho():
    data = request.get_json()
    tipo = data.get('tipo')
    item_id = data.get('id')
    quantidade = data.get('quantidade', 1)
    
    try:
        quantidade = int(quantidade)
        if quantidade < 0 or quantidade > 100:
            return jsonify({'success': False, 'error': 'Quantidade inválida'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Quantidade inválida'}), 400
    
    if 'carrinho' not in session:
        return jsonify({'success': False, 'error': 'Carrinho vazio'}), 400
    
    carrinho = session['carrinho']
    item_encontrado = False
    
    for item in carrinho:
        if item['tipo'] == tipo and item['id'] == item_id:
            if quantidade == 0:
                carrinho.remove(item)
            else:
                if tipo == 'produto':
                    conn = db.get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('SELECT estoque FROM produtos WHERE id = ?', (item_id,))
                    produto = cursor.fetchone()
                    conn.close()
                    
                    if produto and produto['estoque'] < quantidade:
                        return jsonify({'success': False, 'error': 'Estoque insuficiente'}), 400
                
                item['quantidade'] = quantidade
            item_encontrado = True
            break
    
    if not item_encontrado:
        return jsonify({'success': False, 'error': 'Item não encontrado no carrinho'}), 404
    
    session['carrinho'] = carrinho
    session.modified = True
    
    total_itens = sum(item.get('quantidade', 1) for item in carrinho)
    return jsonify({'success': True, 'count': total_itens})

@app.route('/checkout')
@cliente_required
def checkout():
    carrinho_items = session.get('carrinho', [])
    
    if not carrinho_items:
        flash('Seu carrinho está vazio', 'error')
        return redirect(url_for('carrinho'))
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    itens_detalhados = []
    total = 0
    
    for item in carrinho_items:
        if item['tipo'] == 'servico':
            cursor.execute('SELECT * FROM servicos WHERE id = ?', (item['id'],))
            dados = cursor.fetchone()
            if dados:
                preco = dados['preco_promocional'] if dados['promocao'] and dados['preco_promocional'] else dados['preco']
                itens_detalhados.append({
                    'id': dados['id'],
                    'tipo': 'servico',
                    'nome': dados['nome'],
                    'preco': preco,
                    'quantidade': item.get('quantidade', 1),
                    'imagem': dados['imagem']
                })
                total += preco * item.get('quantidade', 1)
        else:
            cursor.execute('SELECT * FROM produtos WHERE id = ?', (item['id'],))
            dados = cursor.fetchone()
            if dados:
                preco = dados['preco_promocional'] if dados['promocao'] and dados['preco_promocional'] else dados['preco']
                itens_detalhados.append({
                    'id': dados['id'],
                    'tipo': 'produto',
                    'nome': dados['nome'],
                    'preco': preco,
                    'quantidade': item.get('quantidade', 1),
                    'imagem': dados['imagem']
                })
                total += preco * item.get('quantidade', 1)
    
    configs = get_configuracoes()
    mercadopago_ativo = configs.get('mercadopago_ativo') == '1'
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in carrinho_items)
    
    return render_template('checkout.html', 
                          itens=itens_detalhados,
                          total=total,
                          carrinho_count=carrinho_count,
                          mercadopago_ativo=mercadopago_ativo)

@app.route('/finalizar-pedido', methods=['POST'])
@cliente_required
def finalizar_pedido():
    data = request.get_json()
    metodo_pagamento = data.get('metodo_pagamento', 'dinheiro')
    observacoes = data.get('observacoes', '')[:500]
    
    carrinho_items = session.get('carrinho', [])
    
    if not carrinho_items:
        return jsonify({'success': False, 'error': 'Carrinho vazio'}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    try:
        itens_detalhados = []
        total = 0
        
        for item in carrinho_items:
            if item['tipo'] == 'servico':
                cursor.execute('SELECT * FROM servicos WHERE id = ? AND ativo = 1', (item['id'],))
                dados = cursor.fetchone()
            else:
                cursor.execute('SELECT * FROM produtos WHERE id = ? AND ativo = 1', (item['id'],))
                dados = cursor.fetchone()
            
            if not dados:
                conn.close()
                return jsonify({'success': False, 'error': f'Item {item["id"]} não encontrado'}), 404
            
            if item['tipo'] == 'produto' and dados['estoque'] < item.get('quantidade', 1):
                conn.close()
                return jsonify({'success': False, 'error': f'Estoque insuficiente para {dados["nome"]}'}), 400
            
            preco = dados['preco_promocional'] if dados['promocao'] and dados['preco_promocional'] else dados['preco']
            quantidade = item.get('quantidade', 1)
            
            itens_detalhados.append({
                'tipo': item['tipo'],
                'item_id': dados['id'],
                'nome': dados['nome'],
                'quantidade': quantidade,
                'valor_unitario': preco,
                'valor_total': preco * quantidade
            })
            
            total += preco * quantidade
        
        cliente_id = session.get('cliente_id')
        
        status_pedido = 'aguardando_confirmacao'
        
        cursor.execute('''INSERT INTO pedidos (cliente_id, valor_total, status, metodo_pagamento, observacoes)
                         VALUES (?, ?, ?, ?, ?)''',
                       (cliente_id, total, status_pedido, metodo_pagamento, observacoes))
        
        pedido_id = cursor.lastrowid
        
        for item in itens_detalhados:
            cursor.execute('''INSERT INTO pedidos_itens (pedido_id, tipo, item_id, nome, quantidade, 
                             valor_unitario, valor_total) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (pedido_id, item['tipo'], item['item_id'], item['nome'], 
                           item['quantidade'], item['valor_unitario'], item['valor_total']))
            
            if item['tipo'] == 'produto':
                cursor.execute('UPDATE produtos SET estoque = estoque - ? WHERE id = ?',
                             (item['quantidade'], item['item_id']))
        
        conn.commit()
        
        session['carrinho'] = []
        session.modified = True
        
        return jsonify({
            'success': True,
            'pedido_id': pedido_id,
            'status': status_pedido
        })
        
    except Exception as e:
        conn.rollback()
        print(f"Erro ao finalizar pedido: {e}")
        return jsonify({'success': False, 'error': 'Erro ao processar pedido'}), 500
    finally:
        conn.close()

@app.route('/agendamento')
def agendamento():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM barbeiros WHERE ativo = 1')
    barbeiros = cursor.fetchall()
    
    cursor.execute('SELECT * FROM servicos WHERE ativo = 1 ORDER BY nome')
    servicos = cursor.fetchall()
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('agendamento.html', 
                          barbeiros=barbeiros,
                          servicos=servicos,
                          carrinho_count=carrinho_count)

@app.route('/horarios-disponiveis', methods=['POST'])
def horarios_disponiveis():
    data = request.get_json()
    barbeiro_id = data.get('barbeiro_id')
    data_selecionada = data.get('data')
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT data_hora FROM agendamentos 
                     WHERE barbeiro_id = ? AND DATE(data_hora) = ? AND status != 'cancelado' ''', 
                     (barbeiro_id, data_selecionada))
    agendamentos_existentes = [row['data_hora'] for row in cursor.fetchall()]
    
    conn.close()
    
    horarios = []
    hora_inicio = 9
    hora_fim = 20
    
    for hora in range(hora_inicio, hora_fim):
        for minuto in [0, 30]:
            horario_str = f"{data_selecionada} {hora:02d}:{minuto:02d}:00"
            if horario_str not in agendamentos_existentes:
                horarios.append(f"{hora:02d}:{minuto:02d}")
    
    return jsonify({'horarios': horarios})

@app.route('/api/admin/check-novos-agendamentos')
@admin_required
def check_novos_agendamentos():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            a.id,
            a.data_hora,
            c.nome as cliente_nome,
            c.telefone as cliente_telefone,
            s.nome as servico_nome,
            b.nome as barbeiro_nome,
            COALESCE(a.valor, COALESCE(s.preco_promocional, s.preco)) as valor,
            a.observacoes,
            a.data_criacao
        FROM agendamentos a
        LEFT JOIN clientes c ON a.cliente_id = c.id
        LEFT JOIN servicos s ON a.servico_id = s.id
        LEFT JOIN barbeiros b ON a.barbeiro_id = b.id
        WHERE a.status != 'cancelado'
        AND datetime(a.data_criacao) >= datetime('now', '-15 seconds')
        ORDER BY a.data_criacao DESC
    ''')
    
    novos_agendamentos = []
    for row in cursor.fetchall():
        novos_agendamentos.append({
            'id': row['id'],
            'data_hora': row['data_hora'],
            'cliente_nome': row['cliente_nome'],
            'cliente_telefone': row['cliente_telefone'],
            'servico_nome': row['servico_nome'],
            'barbeiro_nome': row['barbeiro_nome'],
            'valor': row['valor'],
            'observacoes': row['observacoes'],
            'data_criacao': row['data_criacao']
        })
    
    conn.close()
    
    return jsonify({'novos': novos_agendamentos})

@app.route('/criar-agendamento', methods=['POST'])
def criar_agendamento():
    if 'cliente_id' not in session:
        data = request.get_json()
        session['pending_agendamento'] = data
        session['redirect_after_login'] = '/agendamento'
        return jsonify({'success': False, 'error': 'Para agendar, faça login ou cadastre-se', 'redirect': '/cadastro-cliente', 'require_auth': True}), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
    
    valido, erro = validate_agendamento_data(data)
    if not valido:
        return jsonify({'success': False, 'error': erro}), 400
    
    try:
        data_agendamento = datetime.strptime(data['data'], '%Y-%m-%d').date()
        horario = datetime.strptime(data['horario'], '%H:%M').time()
        data_hora_agendamento = datetime.combine(data_agendamento, horario)
        
        if data_hora_agendamento < datetime.now():
            return jsonify({'success': False, 'error': 'Não é possível agendar em horários passados'}), 400
    except ValueError:
        return jsonify({'success': False, 'error': 'Data ou horário inválido'}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT preco FROM servicos WHERE id = ? AND ativo = 1', (data['servico_id'],))
    servico = cursor.fetchone()
    if not servico:
        conn.close()
        return jsonify({'success': False, 'error': 'Serviço não encontrado'}), 404
    
    cursor.execute('SELECT id FROM barbeiros WHERE id = ? AND ativo = 1', (data['barbeiro_id'],))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Barbeiro não encontrado'}), 404
    
    data_hora = f"{data['data']} {data['horario']}:00"
    
    cursor.execute('''SELECT id FROM agendamentos 
                     WHERE barbeiro_id = ? AND data_hora = ? AND status != 'cancelado' ''',
                     (data['barbeiro_id'], data_hora))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'error': 'Horário já reservado'}), 409
    
    valor = servico['preco']
    observacoes = data.get('observacoes', '')[:500]
    
    cliente_id = session.get('cliente_id')
    
    try:
        cursor.execute('''INSERT INTO agendamentos (cliente_id, barbeiro_id, servico_id, data_hora, 
                         observacoes, valor, status) VALUES (?, ?, ?, ?, ?, ?, 'agendado')''',
                         (cliente_id, data['barbeiro_id'], data['servico_id'], data_hora, 
                          observacoes, valor))
        
        agendamento_id = cursor.lastrowid
        conn.commit()
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'error': 'Erro ao criar agendamento'}), 500
    
    conn.close()
    
    session.pop('pending_agendamento', None)
    
    return jsonify({'success': True, 'agendamento_id': agendamento_id})

@app.route('/obter-agendamento-pendente')
def obter_agendamento_pendente():
    pending_agendamento = session.get('pending_agendamento')
    
    if pending_agendamento:
        session.pop('pending_agendamento', None)
        return jsonify({'success': True, 'agendamento': pending_agendamento})
    return jsonify({'success': False})

@app.route('/historico')
def historico():
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    cliente_id = session.get('cliente_id')
    
    pedidos_com_itens = []
    agendamentos = []
    
    if cliente_id:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''SELECT * FROM pedidos
                         WHERE cliente_id = ?
                         ORDER BY data_criacao DESC''', (cliente_id,))
        pedidos = cursor.fetchall()
        
        for pedido in pedidos:
            cursor.execute('''SELECT * FROM pedidos_itens WHERE pedido_id = ?''', (pedido['id'],))
            itens = cursor.fetchall()
            pedidos_com_itens.append({
                'pedido': dict(pedido),
                'itens': [dict(item) for item in itens]
            })
        
        cursor.execute('''SELECT a.*, b.nome as barbeiro_nome, s.nome as servico_nome
                         FROM agendamentos a
                         LEFT JOIN barbeiros b ON a.barbeiro_id = b.id
                         LEFT JOIN servicos s ON a.servico_id = s.id
                         WHERE a.cliente_id = ?
                         ORDER BY a.data_hora DESC''', (cliente_id,))
        agendamentos = cursor.fetchall()
        
        conn.close()
    
    return render_template('historico.html', 
                          carrinho_count=carrinho_count,
                          pedidos=pedidos_com_itens,
                          agendamentos=agendamentos)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now().strftime('%Y-%m-%d')
    data_filtro = request.args.get('data', None)
    
    cursor.execute('''SELECT COUNT(*) as total FROM agendamentos 
                     WHERE DATE(data_hora) = ? AND status != 'cancelado' ''', (hoje,))
    agendamentos_hoje = cursor.fetchone()['total']
    
    cursor.execute('''SELECT SUM(valor_total) as total FROM vendas 
                     WHERE DATE(data_venda) = ?''', (hoje,))
    faturamento = cursor.fetchone()
    faturamento_hoje = faturamento['total'] if faturamento['total'] else 0
    
    cursor.execute('SELECT COUNT(*) as total FROM clientes')
    total_clientes = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM produtos WHERE estoque <= estoque_minimo')
    produtos_baixo_estoque = cursor.fetchone()['total']
    
    if data_filtro:
        cursor.execute('''SELECT a.*, b.nome as barbeiro_nome, s.nome as servico_nome, 
                         c.nome as cliente_nome,
                         COALESCE(a.valor, COALESCE(s.preco_promocional, s.preco)) as valor_exibir
                         FROM agendamentos a
                         LEFT JOIN barbeiros b ON a.barbeiro_id = b.id
                         LEFT JOIN servicos s ON a.servico_id = s.id
                         LEFT JOIN clientes c ON a.cliente_id = c.id
                         WHERE DATE(a.data_hora) = ? AND a.status != 'cancelado'
                         ORDER BY a.data_hora''', (data_filtro,))
    else:
        cursor.execute('''SELECT a.*, b.nome as barbeiro_nome, s.nome as servico_nome, 
                         c.nome as cliente_nome,
                         COALESCE(a.valor, COALESCE(s.preco_promocional, s.preco)) as valor_exibir
                         FROM agendamentos a
                         LEFT JOIN barbeiros b ON a.barbeiro_id = b.id
                         LEFT JOIN servicos s ON a.servico_id = s.id
                         LEFT JOIN clientes c ON a.cliente_id = c.id
                         WHERE DATE(a.data_hora) >= ? AND a.status != 'cancelado'
                         ORDER BY a.data_hora''', (hoje,))
    
    agendamentos = cursor.fetchall()
    
    cursor.execute('SELECT * FROM produtos WHERE estoque <= estoque_minimo')
    estoque_alerta = cursor.fetchall()
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                          agendamentos_hoje=agendamentos_hoje,
                          faturamento_hoje=faturamento_hoje,
                          total_clientes=total_clientes,
                          produtos_baixo_estoque=produtos_baixo_estoque,
                          agendamentos=agendamentos,
                          estoque_alerta=estoque_alerta,
                          data_filtro=data_filtro,
                          hoje=hoje)

@app.route('/admin/servicos')
@admin_required
def admin_servicos():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT s.*, c.nome as categoria_nome FROM servicos s
                     LEFT JOIN categorias c ON s.categoria_id = c.id
                     ORDER BY s.nome''')
    servicos = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM categorias WHERE ativo = 1')
    categorias = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin/servicos.html', 
                          servicos=servicos,
                          categorias=categorias)

@app.route('/admin/produtos')
@admin_required
def admin_produtos():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT p.*, c.nome as categoria_nome FROM produtos p
                     LEFT JOIN categorias c ON p.categoria_id = c.id
                     ORDER BY p.nome''')
    produtos = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute('SELECT * FROM categorias WHERE ativo = 1')
    categorias = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin/produtos.html', 
                          produtos=produtos,
                          categorias=categorias)

@app.route('/admin/barbeiros')
@admin_required
def admin_barbeiros():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM barbeiros ORDER BY nome')
    barbeiros = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin/barbeiros.html', barbeiros=barbeiros)

@app.route('/admin/barbeiros/atualizar-comissao', methods=['POST'])
@admin_required
def atualizar_comissao_barbeiro():
    barbeiro_id = request.form.get('barbeiro_id')
    comissao_tipo = request.form.get('comissao_tipo')
    comissao_valor = request.form.get('comissao_valor')
    
    if not barbeiro_id or not comissao_tipo or not comissao_valor:
        flash('Todos os campos são obrigatórios', 'error')
        return redirect(url_for('admin_barbeiros'))
    
    if comissao_tipo not in ['percentual', 'fixa']:
        flash('Tipo de comissão inválido', 'error')
        return redirect(url_for('admin_barbeiros'))
    
    try:
        comissao_valor_float = float(comissao_valor)
        if comissao_valor_float < 0:
            flash('Valor da comissão não pode ser negativo', 'error')
            return redirect(url_for('admin_barbeiros'))
        
        if comissao_tipo == 'percentual' and comissao_valor_float > 100:
            flash('Comissão percentual não pode ser maior que 100%', 'error')
            return redirect(url_for('admin_barbeiros'))
    except ValueError:
        flash('Valor de comissão inválido', 'error')
        return redirect(url_for('admin_barbeiros'))
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''UPDATE barbeiros 
                         SET comissao_tipo = ?, comissao_valor = ? 
                         WHERE id = ?''',
                      (comissao_tipo, comissao_valor_float, barbeiro_id))
        conn.commit()
        flash('Comissão atualizada com sucesso!', 'success')
    except Exception as e:
        conn.rollback()
        flash('Erro ao atualizar comissão', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('admin_barbeiros'))

@app.route('/admin/configuracoes', methods=['GET', 'POST'])
@admin_required
def admin_configuracoes():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        campos = [
            'nome_barbearia', 'logo_emoji', 'logo_url', 'horario_abertura', 'horario_fechamento',
            'telefone', 'whatsapp', 'email', 'endereco', 'cidade', 'estado', 'cep',
            'instagram', 'facebook', 'descricao', 'tempo_atendimento', 'status_aberto',
            'dias_funcionamento', 'mercadopago_ativo'
        ]
        
        try:
            for campo in campos:
                valor = request.form.get(campo, '').strip()
                cursor.execute('''INSERT INTO configuracoes (chave, valor) VALUES (?, ?)
                                 ON CONFLICT(chave) DO UPDATE SET valor = ?''',
                             (campo, valor, valor))
            
            conn.commit()
            flash('Configurações atualizadas com sucesso!', 'success')
        except Exception as e:
            conn.rollback()
            flash('Erro ao atualizar configurações', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('admin_configuracoes'))
    
    cursor.execute('SELECT * FROM configuracoes')
    configs_raw = cursor.fetchall()
    conn.close()
    
    configs = {}
    for config in configs_raw:
        configs[config['chave']] = config['valor']
    
    mercadopago_configured = bool(os.getenv('MERCADOPAGO_ACCESS_TOKEN'))
    
    return render_template('admin/configuracoes.html', 
                         configs=configs,
                         mercadopago_configured=mercadopago_configured)

@app.route('/admin/pedidos')
@admin_required
def admin_pedidos():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''SELECT p.*, c.nome as cliente_nome, c.telefone as cliente_telefone
                     FROM pedidos p
                     LEFT JOIN clientes c ON p.cliente_id = c.id
                     ORDER BY p.data_criacao DESC
                     LIMIT 100''')
    pedidos = cursor.fetchall()
    
    pedidos_com_itens = []
    for pedido in pedidos:
        cursor.execute('''SELECT * FROM pedidos_itens WHERE pedido_id = ?''', (pedido['id'],))
        itens = cursor.fetchall()
        pedidos_com_itens.append({
            'pedido': dict(pedido),
            'itens': [dict(item) for item in itens]
        })
    
    conn.close()
    
    return render_template('admin/pedidos.html', pedidos=pedidos_com_itens)

@app.route('/admin/confirmar-pagamento', methods=['POST'])
@admin_required
def admin_confirmar_pagamento():
    data = request.get_json()
    pedido_id = data.get('pedido_id')
    
    if not pedido_id:
        return jsonify({'success': False, 'error': 'ID do pedido não fornecido'}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''SELECT * FROM pedidos 
                         WHERE id = ? AND status = 'aguardando_confirmacao' ''', (pedido_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return jsonify({'success': False, 'error': 'Pedido não encontrado ou já confirmado'}), 404
        
        cursor.execute('''UPDATE pedidos SET status = 'pago', data_atualizacao = CURRENT_TIMESTAMP
                         WHERE id = ?''', (pedido_id,))
        
        cursor.execute('''SELECT * FROM pedidos_itens WHERE pedido_id = ?''', (pedido_id,))
        itens = cursor.fetchall()
        
        for item in itens:
            cursor.execute('''INSERT INTO vendas (cliente_id, tipo, item_id, quantidade, 
                             valor_unitario, valor_total, metodo_pagamento, status)
                             VALUES (?, ?, ?, ?, ?, ?, ?, 'concluido')''',
                          (pedido['cliente_id'], item['tipo'], item['item_id'], 
                           item['quantidade'], item['valor_unitario'], item['valor_total'],
                           pedido['metodo_pagamento']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print(f"Erro ao confirmar pagamento: {e}")
        return jsonify({'success': False, 'error': 'Erro ao confirmar pagamento'}), 500
    finally:
        conn.close()

@app.route('/admin/cancelar-pedido', methods=['POST'])
@admin_required
def admin_cancelar_pedido():
    data = request.get_json()
    pedido_id = data.get('pedido_id')
    
    if not pedido_id:
        return jsonify({'success': False, 'error': 'ID do pedido não fornecido'}), 400
    
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM pedidos_itens WHERE pedido_id = ?', (pedido_id,))
        itens = cursor.fetchall()
        
        for item in itens:
            if item['tipo'] == 'produto':
                cursor.execute('UPDATE produtos SET estoque = estoque + ? WHERE id = ?',
                             (item['quantidade'], item['item_id']))
        
        cursor.execute('''UPDATE pedidos SET status = 'cancelado', data_atualizacao = CURRENT_TIMESTAMP
                         WHERE id = ?''', (pedido_id,))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cancelar pedido: {e}")
        return jsonify({'success': False, 'error': 'Erro ao cancelar pedido'}), 500
    finally:
        conn.close()

@app.route('/contato')
def contato():
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    return render_template('contato.html', carrinho_count=carrinho_count)

@app.route('/login-cliente', methods=['GET', 'POST'])
def login_cliente():
    carrinho = session.get('carrinho') or []
    carrinho_count = len(carrinho)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        
        if not nome or not telefone:
            flash('Nome e telefone são obrigatórios', 'error')
            return render_template('login-cliente.html', carrinho_count=carrinho_count)
        
        if len(nome) < 3:
            flash('Nome deve ter pelo menos 3 caracteres', 'error')
            return render_template('login-cliente.html', carrinho_count=carrinho_count)
        
        telefone_limpo = re.sub(r'\D', '', telefone)
        if len(telefone_limpo) < 10:
            flash('Telefone inválido', 'error')
            return render_template('login-cliente.html', carrinho_count=carrinho_count)
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM clientes WHERE nome = ? AND telefone = ?', (nome, telefone))
        cliente = cursor.fetchone()
        conn.close()
        
        if cliente:
            carrinho_temp = session.get('carrinho', [])
            pending_agendamento = session.get('pending_agendamento')
            redirect_url = session.get('redirect_after_login')
            
            session.clear()
            session['cliente_id'] = cliente['id']
            session['cliente_nome'] = cliente['nome']
            session['cliente_telefone'] = cliente['telefone']
            session.permanent = True
            
            if carrinho_temp:
                session['carrinho'] = carrinho_temp
            
            if pending_agendamento:
                session['pending_agendamento'] = pending_agendamento
            
            flash('Login realizado com sucesso!', 'success')
            
            if redirect_url:
                if pending_agendamento:
                    return redirect(redirect_url + '?processar_agendamento=true')
                return redirect(redirect_url)
            return redirect(url_for('index'))
        else:
            flash('Nome ou telefone incorretos. Verifique se digitou exatamente como cadastrado.', 'error')
    
    return render_template('login-cliente.html', carrinho_count=carrinho_count)

@app.route('/login-admin', methods=['GET', 'POST'])
@app.route('/admin/login', methods=['GET', 'POST'])
def login_admin():
    carrinho = session.get('carrinho') or []
    carrinho_count = len(carrinho)
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        
        if not email or not senha:
            flash('Email e senha são obrigatórios', 'error')
            return render_template('login-admin.html', carrinho_count=carrinho_count)
        
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Email inválido', 'error')
            return render_template('login-admin.html', carrinho_count=carrinho_count)
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM administradores WHERE email = ? AND ativo = 1', (email,))
        admin = cursor.fetchone()
        conn.close()
        
        if admin and admin['senha'] and check_password_hash(admin['senha'], senha):
            session.clear()
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            session['admin_nome'] = admin['nome']
            session['admin_email'] = admin['email']
            session.permanent = True
            
            flash('Bem-vindo ao painel administrativo!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Email ou senha incorretos', 'error')
    
    return render_template('login-admin.html', carrinho_count=carrinho_count)

@app.route('/cadastro')
def cadastro():
    return redirect(url_for('cadastro_cliente'))

@app.route('/cadastro-cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    carrinho = session.get('carrinho') or []
    carrinho_count = len(carrinho)
    
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        telefone = request.form.get('telefone', '').strip()
        
        if not nome or not telefone:
            flash('Nome e telefone são obrigatórios', 'error')
            return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)
        
        if len(nome) < 3:
            flash('Nome deve ter pelo menos 3 caracteres', 'error')
            return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)
        
        telefone_limpo = re.sub(r'\D', '', telefone)
        if len(telefone_limpo) < 10:
            flash('Telefone deve ter pelo menos 10 dígitos', 'error')
            return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM clientes WHERE telefone = ?', (telefone,))
        if cursor.fetchone():
            conn.close()
            flash('Este telefone já está cadastrado', 'error')
            return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)
        
        try:
            cursor.execute('''INSERT INTO clientes (nome, telefone) 
                            VALUES (?, ?)''', (nome, telefone))
            cliente_id = cursor.lastrowid
            conn.commit()
            
            carrinho_temp = session.get('carrinho', [])
            pending_agendamento = session.get('pending_agendamento')
            redirect_url = session.get('redirect_after_login')
            
            session.clear()
            session['cliente_id'] = cliente_id
            session['cliente_nome'] = nome
            session['cliente_telefone'] = telefone
            session.permanent = True
            
            if carrinho_temp:
                session['carrinho'] = carrinho_temp
            
            if pending_agendamento:
                session['pending_agendamento'] = pending_agendamento
            
            flash('Cadastro realizado com sucesso!', 'success')
            
            if redirect_url:
                if pending_agendamento:
                    return redirect(redirect_url + '?processar_agendamento=true')
                return redirect(redirect_url)
            return redirect(url_for('index'))
        except Exception as e:
            conn.rollback()
            flash('Erro ao criar cadastro. Tente novamente.', 'error')
            return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)
        finally:
            conn.close()
    
    return render_template('cadastro-cliente.html', carrinho_count=carrinho_count)

@app.route('/logout')
def logout():
    session.pop('cliente_id', None)
    session.pop('cliente_nome', None)
    session.pop('cliente_email', None)
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    session.pop('admin_nome', None)
    session.pop('admin_email', None)
    flash('Você saiu da sua conta', 'success')
    return redirect(url_for('index'))

@app.route('/perfil')
@cliente_required
def perfil():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clientes WHERE id = ?', (session['cliente_id'],))
    cliente = cursor.fetchone()
    
    cursor.execute('''SELECT a.*, b.nome as barbeiro_nome, s.nome as servico_nome
                     FROM agendamentos a
                     LEFT JOIN barbeiros b ON a.barbeiro_id = b.id
                     LEFT JOIN servicos s ON a.servico_id = s.id
                     WHERE a.cliente_id = ?
                     ORDER BY a.data_hora DESC
                     LIMIT 10''', (session['cliente_id'],))
    agendamentos = cursor.fetchall()
    
    conn.close()
    carrinho_count = sum(item.get('quantidade', 1) for item in session.get('carrinho', []))
    
    return render_template('perfil.html', 
                          cliente=cliente, 
                          agendamentos=agendamentos,
                          carrinho_count=carrinho_count)

@app.route('/admin/api/produtos', methods=['POST'])
@admin_required
def criar_produto():
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        preco = float(data.get('preco', 0))
        estoque = int(data.get('estoque', 0))
        estoque_minimo = int(data.get('estoque_minimo', 0))
        categoria_id = data.get('categoria_id')
        imagem = data.get('imagem', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome or preco <= 0:
            return jsonify({'success': False, 'message': 'Nome e preço são obrigatórios'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO produtos (nome, descricao, preco, estoque, estoque_minimo, categoria_id, imagem, ativo)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (nome, descricao, preco, estoque, estoque_minimo, categoria_id if categoria_id else None, imagem, ativo))
        conn.commit()
        conn.close()
        
        flash('Produto adicionado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/produtos/<int:id>', methods=['POST'])
@admin_required
def editar_produto(id):
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        preco = float(data.get('preco', 0))
        estoque = int(data.get('estoque', 0))
        estoque_minimo = int(data.get('estoque_minimo', 0))
        categoria_id = data.get('categoria_id')
        imagem = data.get('imagem', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome or preco <= 0:
            return jsonify({'success': False, 'message': 'Nome e preço são obrigatórios'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''UPDATE produtos SET nome=?, descricao=?, preco=?, estoque=?, estoque_minimo=?, 
                         categoria_id=?, imagem=?, ativo=? WHERE id=?''',
                      (nome, descricao, preco, estoque, estoque_minimo, categoria_id if categoria_id else None, imagem, ativo, id))
        conn.commit()
        conn.close()
        
        flash('Produto atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/produtos/<int:id>/deletar', methods=['POST'])
@admin_required
def deletar_produto(id):
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produtos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        flash('Produto deletado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/servicos', methods=['POST'])
@admin_required
def criar_servico():
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        preco = float(data.get('preco', 0))
        duracao_minutos = int(data.get('duracao', 30))
        categoria_id = data.get('categoria_id')
        imagem = data.get('imagem', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome or preco <= 0:
            return jsonify({'success': False, 'message': 'Nome e preço são obrigatórios'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO servicos (nome, descricao, preco, duracao_minutos, categoria_id, imagem, ativo)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (nome, descricao, preco, duracao_minutos, categoria_id if categoria_id else None, imagem, ativo))
        conn.commit()
        conn.close()
        
        flash('Serviço adicionado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/servicos/<int:id>', methods=['POST'])
@admin_required
def editar_servico(id):
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        preco = float(data.get('preco', 0))
        duracao_minutos = int(data.get('duracao', 30))
        categoria_id = data.get('categoria_id')
        imagem = data.get('imagem', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome or preco <= 0:
            return jsonify({'success': False, 'message': 'Nome e preço são obrigatórios'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''UPDATE servicos SET nome=?, descricao=?, preco=?, duracao_minutos=?, 
                         categoria_id=?, imagem=?, ativo=? WHERE id=?''',
                      (nome, descricao, preco, duracao_minutos, categoria_id if categoria_id else None, imagem, ativo, id))
        conn.commit()
        conn.close()
        
        flash('Serviço atualizado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/servicos/<int:id>/deletar', methods=['POST'])
@admin_required
def deletar_servico(id):
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM servicos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        flash('Serviço deletado com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/categorias')
@admin_required
def admin_categorias():
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categorias ORDER BY nome')
    categorias = cursor.fetchall()
    conn.close()
    return render_template('admin/categorias.html', categorias=categorias)

@app.route('/admin/api/categorias', methods=['POST'])
@admin_required
def criar_categoria():
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        tipo = data.get('tipo', 'produto')
        icone = data.get('icone', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO categorias (nome, descricao, tipo, icone, ativo)
                         VALUES (?, ?, ?, ?, ?)''',
                      (nome, descricao, tipo, icone, ativo))
        conn.commit()
        conn.close()
        
        flash('Categoria adicionada com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/categorias/<int:id>', methods=['POST'])
@admin_required
def editar_categoria(id):
    try:
        data = request.form
        nome = data.get('nome', '').strip()
        descricao = data.get('descricao', '').strip()
        tipo = data.get('tipo', 'produto')
        icone = data.get('icone', '').strip()
        ativo = data.get('ativo') == '1'
        
        if not nome:
            return jsonify({'success': False, 'message': 'Nome é obrigatório'}), 400
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''UPDATE categorias SET nome=?, descricao=?, tipo=?, icone=?, ativo=? WHERE id=?''',
                      (nome, descricao, tipo, icone, ativo, id))
        conn.commit()
        conn.close()
        
        flash('Categoria atualizada com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/api/categorias/<int:id>/deletar', methods=['POST'])
@admin_required
def deletar_categoria(id):
    try:
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categorias WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        flash('Categoria deletada com sucesso!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.template_filter('datetime_format')
def datetime_format_filter(value):
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except:
            try:
                dt = datetime.fromisoformat(value)
            except:
                return value
    else:
        dt = value
    
    return dt.strftime('%d/%m/%Y às %H:%M')

@app.template_filter('date_format')
def date_format_filter(value):
    if isinstance(value, str):
        try:
            dt = datetime.strptime(value, '%Y-%m-%d')
        except:
            try:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            except:
                try:
                    dt = datetime.fromisoformat(value)
                except:
                    return value
    else:
        dt = value
    
    return dt.strftime('%d/%m/%Y')

@app.template_filter('currency')
def currency_filter(value):
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
