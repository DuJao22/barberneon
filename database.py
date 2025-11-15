import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = 'database/barbearia.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            tipo TEXT DEFAULT 'produto',
            icone TEXT,
            ordem INTEGER DEFAULT 0,
            ativo INTEGER DEFAULT 1
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            duracao_minutos INTEGER DEFAULT 30,
            imagem TEXT,
            categoria_id INTEGER,
            ativo INTEGER DEFAULT 1,
            destaque INTEGER DEFAULT 0,
            promocao INTEGER DEFAULT 0,
            preco_promocional REAL,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            estoque INTEGER DEFAULT 0,
            estoque_minimo INTEGER DEFAULT 5,
            imagem TEXT,
            categoria_id INTEGER,
            ativo INTEGER DEFAULT 1,
            destaque INTEGER DEFAULT 0,
            promocao INTEGER DEFAULT 0,
            preco_promocional REAL,
            FOREIGN KEY (categoria_id) REFERENCES categorias(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS barbeiros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            foto TEXT,
            especialidade TEXT,
            telefone TEXT,
            email TEXT,
            comissao_tipo TEXT DEFAULT 'percentual' CHECK (comissao_tipo IN ('percentual', 'fixa')),
            comissao_valor REAL DEFAULT 50.0,
            ativo INTEGER DEFAULT 1,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT UNIQUE NOT NULL,
            pontos_fidelidade INTEGER DEFAULT 0,
            total_gasto REAL DEFAULT 0,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
            ultima_visita TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agendamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            barbeiro_id INTEGER,
            servico_id INTEGER,
            data_hora TEXT NOT NULL,
            status TEXT DEFAULT 'agendado',
            observacoes TEXT,
            valor REAL,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (barbeiro_id) REFERENCES barbeiros(id),
            FOREIGN KEY (servico_id) REFERENCES servicos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fila_virtual (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            cliente_telefone TEXT,
            servico_id INTEGER,
            posicao INTEGER,
            status TEXT DEFAULT 'aguardando',
            data_entrada TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (servico_id) REFERENCES servicos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            barbeiro_id INTEGER,
            tipo TEXT,
            item_id INTEGER,
            quantidade INTEGER DEFAULT 1,
            valor_unitario REAL,
            valor_total REAL,
            metodo_pagamento TEXT,
            status TEXT DEFAULT 'concluido',
            data_venda TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id),
            FOREIGN KEY (barbeiro_id) REFERENCES barbeiros(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            valor_total REAL NOT NULL,
            status TEXT DEFAULT 'pendente_pagamento',
            metodo_pagamento TEXT,
            mercadopago_preference_id TEXT,
            mercadopago_payment_id TEXT,
            observacoes TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            data_atualizacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            quantidade INTEGER DEFAULT 1,
            valor_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracoes (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS administradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            ativo INTEGER DEFAULT 1,
            data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def popular_dados_exemplo():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM categorias")
    if cursor.fetchone()['count'] == 0:
        categorias = [
            ('Mais Vendidos', '⭐', 1),
            ('Promoções', '🔥', 2),
            ('Cortes Premium', '✂️', 3),
            ('Barba & Bigode', '🧔', 4),
            ('Produtos para Cabelo', '💈', 5),
            ('Produtos para Barba', '🧴', 6)
        ]
        cursor.executemany('INSERT INTO categorias (nome, icone, ordem) VALUES (?, ?, ?)', categorias)
        
        servicos = [
            ('Corte Degradê', 'Corte moderno com degradê, ajustado ao seu estilo', 45.00, 45, None, 3, 1, 1, 0, None),
            ('Corte + Barba', 'Combo completo: corte de cabelo + barba aparada e finalizada', 65.00, 60, None, 1, 1, 1, 1, 55.00),
            ('Barba Completa', 'Barba aparada, contornos definidos e hidratação', 30.00, 30, None, 4, 1, 0, 0, None),
            ('Corte Tesoura', 'Corte tradicional na tesoura, perfeito para estilos clássicos', 50.00, 50, None, 3, 1, 1, 0, None),
            ('Platinado', 'Descoloração completa com tonalização', 120.00, 120, None, 3, 1, 0, 1, 100.00),
            ('Design de Barba', 'Desenhos e contornos especiais na barba', 25.00, 20, None, 4, 1, 0, 0, None),
            ('Sobrancelha', 'Design e limpeza de sobrancelhas masculinas', 20.00, 15, None, 3, 1, 0, 0, None),
            ('Luzes', 'Mechas e luzes para destacar o visual', 80.00, 90, None, 3, 1, 0, 0, None)
        ]
        cursor.executemany('''INSERT INTO servicos (nome, descricao, preco, duracao_minutos, imagem, 
                            categoria_id, ativo, destaque, promocao, preco_promocional) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', servicos)
        
        produtos = [
            ('Pomada Modeladora Premium', 'Fixação forte, acabamento natural, 100g', 45.00, 25, 10, None, 5, 1, 1, 0, None),
            ('Shampoo Anticaspa', 'Limpeza profunda e controle da caspa, 300ml', 35.00, 15, 10, None, 5, 1, 0, 0, None),
            ('Óleo para Barba', 'Hidratação e brilho para barbas, 30ml', 40.00, 20, 10, None, 6, 1, 1, 1, 35.00),
            ('Cera Modeladora', 'Fixação média, fácil aplicação, 80g', 38.00, 30, 10, None, 5, 1, 0, 0, None),
            ('Balm para Barba', 'Hidratação profunda e amaciamento, 60g', 42.00, 18, 10, None, 6, 1, 0, 0, None),
            ('Kit Navalha Premium', 'Kit completo com navalha profissional e suporte', 95.00, 8, 5, None, 6, 1, 0, 1, 80.00),
            ('Pente de Madeira', 'Pente antiestático de madeira nobre', 25.00, 12, 10, None, 5, 1, 0, 0, None),
            ('Escova Modeladora', 'Escova profissional para modelar e finalizar', 55.00, 10, 10, None, 5, 1, 0, 0, None)
        ]
        cursor.executemany('''INSERT INTO produtos (nome, descricao, preco, estoque, estoque_minimo, imagem,
                            categoria_id, ativo, destaque, promocao, preco_promocional)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', produtos)
        
        barbeiros = [
            ('Carlos Silva', None, 'Degradê e cortes modernos', '(11) 98765-4321', 'carlos@barbearia.com', 'percentual', 50.0, 1),
            ('João Santos', None, 'Barba e acabamentos', '(11) 98765-4322', 'joao@barbearia.com', 'percentual', 50.0, 1),
            ('Pedro Oliveira', None, 'Cortes clássicos', '(11) 98765-4323', 'pedro@barbearia.com', 'percentual', 50.0, 1),
            ('Lucas Martins', None, 'Coloração e platinados', '(11) 98765-4324', 'lucas@barbearia.com', 'percentual', 55.0, 1)
        ]
        cursor.executemany('''INSERT INTO barbeiros (nome, foto, especialidade, telefone, email, 
                            comissao_tipo, comissao_valor, ativo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', barbeiros)
        
        cursor.execute("SELECT COUNT(*) as count FROM configuracoes")
        if cursor.fetchone()['count'] == 0:
            cursor.execute('''INSERT INTO configuracoes (chave, valor) VALUES 
                        ('nome_barbearia', 'Barbearia Premium'),
                        ('logo_emoji', '💈'),
                        ('horario_abertura', '09:00'),
                        ('horario_fechamento', '20:00'),
                        ('dias_funcionamento', '1,2,3,4,5,6'),
                        ('status_aberto', '1'),
                        ('telefone', '(11) 3456-7890'),
                        ('whatsapp', '(11) 98765-4321'),
                        ('email', 'contato@barbearia.com'),
                        ('endereco', 'Rua da Barbearia, 123 - Centro'),
                        ('cidade', 'São Paulo'),
                        ('estado', 'SP'),
                        ('cep', '01234-567'),
                        ('instagram', '@barbeariapremuim'),
                        ('facebook', 'BarbeariaPremium'),
                        ('descricao', 'A melhor barbearia da cidade! Cortes modernos, atendimento premium e produtos de qualidade.'),
                        ('tempo_atendimento', '30'),
                        ('mercadopago_ativo', '0'),
                        ('mercadopago_access_token', ''),
                        ('mercadopago_public_key', '')''')
        
        cursor.execute("SELECT COUNT(*) as count FROM administradores")
        if cursor.fetchone()['count'] == 0:
            admin_senha_hash = generate_password_hash('admin123')
            cursor.execute('''INSERT INTO administradores (nome, email, senha) 
                            VALUES (?, ?, ?)''', ('Administrador', 'admin@barbearia.com', admin_senha_hash))
    
    conn.commit()
    conn.close()

def migrar_banco_existente():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(clientes)")
        colunas_clientes = [col[1] for col in cursor.fetchall()]
        
        if 'email' in colunas_clientes or 'senha' in colunas_clientes:
            cursor.execute("DROP TABLE IF EXISTS clientes_old")
            cursor.execute("ALTER TABLE clientes RENAME TO clientes_old")
            
            cursor.execute('''
                CREATE TABLE clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    telefone TEXT UNIQUE NOT NULL,
                    pontos_fidelidade INTEGER DEFAULT 0,
                    total_gasto REAL DEFAULT 0,
                    data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP,
                    ultima_visita TEXT
                )
            ''')
            
            cursor.execute('''
                INSERT INTO clientes (id, nome, telefone, pontos_fidelidade, total_gasto, data_cadastro, ultima_visita)
                SELECT id, nome, COALESCE(telefone, '(00) 00000-0000'), pontos_fidelidade, total_gasto, data_cadastro, ultima_visita
                FROM clientes_old
            ''')
            
            cursor.execute("DROP TABLE clientes_old")
            print("Tabela clientes migrada com sucesso!")
        
        cursor.execute("PRAGMA table_info(barbeiros)")
        colunas_barbeiros = [col[1] for col in cursor.fetchall()]
        
        if 'comissao_percentual' in colunas_barbeiros and 'comissao_tipo' not in colunas_barbeiros:
            cursor.execute("DROP TABLE IF EXISTS barbeiros_old")
            cursor.execute("ALTER TABLE barbeiros RENAME TO barbeiros_old")
            
            cursor.execute('''
                CREATE TABLE barbeiros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    foto TEXT,
                    especialidade TEXT,
                    telefone TEXT,
                    email TEXT,
                    comissao_tipo TEXT DEFAULT 'percentual' CHECK (comissao_tipo IN ('percentual', 'fixa')),
                    comissao_valor REAL DEFAULT 50.0,
                    ativo INTEGER DEFAULT 1,
                    data_cadastro TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO barbeiros (id, nome, foto, especialidade, telefone, email, comissao_tipo, comissao_valor, ativo, data_cadastro)
                SELECT id, nome, foto, especialidade, telefone, email, 'percentual', comissao_percentual, ativo, data_cadastro
                FROM barbeiros_old
            ''')
            
            cursor.execute("DROP TABLE barbeiros_old")
            print("Tabela barbeiros migrada com sucesso!")
        
        configuracoes_mercadopago = [
            'mercadopago_ativo',
            'mercadopago_access_token',
            'mercadopago_public_key'
        ]
        
        for config in configuracoes_mercadopago:
            cursor.execute("SELECT chave FROM configuracoes WHERE chave = ?", (config,))
            if not cursor.fetchone():
                valor_padrao = '0' if config == 'mercadopago_ativo' else ''
                cursor.execute("INSERT INTO configuracoes (chave, valor) VALUES (?, ?)", (config, valor_padrao))
                print(f"Configuração '{config}' adicionada!")
        
        conn.commit()
        print("Migração concluída com sucesso!")
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_database()
    popular_dados_exemplo()
    migrar_banco_existente()
    print("Banco de dados criado e populado com sucesso!")
