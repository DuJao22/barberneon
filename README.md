# Sistema de Gestão para Barbearia

Sistema completo de gestão para barbearia desenvolvido em Python/Flask com SQLite3, design mobile-first com tema preto e azul neon, inspirado em aplicativos de delivery.

## 🚀 Características

- ✅ Design mobile-first responsivo com tema preto (#000000) e azul neon (#00D9FF)
- ✅ Interface inspirada em aplicativos de delivery (estilo La Banquinha)
- ✅ Backend Flask com SQLite3 puro (sem SQLAlchemy)
- ✅ Sistema de autenticação para área administrativa
- ✅ Validação de dados e proteção contra SQL injection
- ✅ Otimizado para deploy no Render

## 📋 Funcionalidades

### Interface do Cliente
- Catálogo de serviços e produtos com categorias
- Sistema de busca
- Carrinho de compras com persistência em sessão
- Agendamento online com seleção de barbeiro e horário
- Histórico de agendamentos
- Status de funcionamento (Aberto/Fechado)

### Painel Administrativo (Protegido por Senha)
- Dashboard com estatísticas em tempo real
- Gestão de serviços (cortes, barba, etc.)
- Gestão de produtos (pomadas, shampoos, etc.)
- Gestão de barbeiros
- Controle de agendamentos
- Alertas de estoque baixo
- Relatórios financeiros

## 🔧 Configuração e Instalação

### Requisitos
- Python 3.11+
- pip

### Instalação Local

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd <pasta-do-projeto>
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- `SESSION_SECRET`: Chave secreta para sessões (gere com: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `ADMIN_PASSWORD`: Senha do painel administrativo

4. Inicialize o banco de dados:
```bash
python database.py
```

5. Execute o servidor:
```bash
python app.py
```

Acesse: `http://localhost:5000`

## 🚢 Deploy no Render

### Variáveis de Ambiente Obrigatórias

Configure no painel do Render:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `SESSION_SECRET` | Chave secreta para sessões | `a1b2c3d4e5f6...` (64 caracteres) |
| `ADMIN_PASSWORD` | Senha do painel admin | `SuaSenhaForte123!` |

### Passos para Deploy

1. Conecte seu repositório ao Render
2. Configure como **Web Service**
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn app:app --bind 0.0.0.0:5000 --workers 2`
5. Configure as variáveis de ambiente
6. Deploy!

O sistema automaticamente:
- Cria o banco de dados SQLite3
- Popula com dados de exemplo
- Inicia o servidor Gunicorn

## 🔐 Segurança

- ✅ Autenticação obrigatória para painel administrativo
- ✅ Validação de todos os dados de entrada
- ✅ Proteção contra SQL injection (uso de parametrização)
- ✅ Verificação de estoque antes de adicionar ao carrinho
- ✅ Validação de conflitos de horário em agendamentos
- ✅ Session secret obrigatória em produção
- ✅ Sanitização de observações (limite de 500 caracteres)

## 📱 Acesso ao Sistema

### Cliente
- URL: `https://seu-app.onrender.com/`
- Navegação livre por catálogo, produtos e serviços
- Agendamento e carrinho disponíveis sem login

### Administrador
- URL: `https://seu-app.onrender.com/admin/login`
- Senha padrão: `admin123` (ALTERE IMEDIATAMENTE)
- Configure `ADMIN_PASSWORD` nas variáveis de ambiente

## 🎨 Tema Visual

- **Background**: Preto puro (#000000)
- **Destaque**: Azul neon (#00D9FF)
- **Sucesso**: Verde neon (#00FF88)
- **Erro**: Vermelho neon (#FF0055)
- **Ação**: Amarelo neon (#FFD700)

## 📊 Estrutura do Banco de Dados

- **categorias**: Categorias de serviços/produtos
- **servicos**: Serviços oferecidos (cortes, barba, etc.)
- **produtos**: Produtos para venda (pomadas, shampoos)
- **barbeiros**: Profissionais da barbearia
- **clientes**: Cadastro de clientes
- **agendamentos**: Agendamentos de horários
- **fila_virtual**: Fila de espera para clientes sem agendamento
- **vendas**: Registro de vendas realizadas
- **configuracoes**: Configurações do sistema

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask 3.0.0, Python 3.11
- **Banco de Dados**: SQLite3
- **Frontend**: HTML5, CSS3, JavaScript Vanilla
- **Servidor**: Gunicorn
- **Deploy**: Render

## 📝 Dados de Exemplo

O sistema vem com dados de exemplo:
- 6 categorias
- 8 serviços (cortes, barba, etc.)
- 8 produtos (pomadas, óleos, etc.)
- 4 barbeiros

## 🔄 Próximas Funcionalidades

- [ ] Sistema de autenticação de clientes
- [ ] Notificações via WhatsApp
- [ ] Programa de fidelidade
- [ ] Relatórios avançados
- [ ] Multi-unidades
- [ ] API REST

## 📄 Licença

Este projeto está sob licença MIT.

## 🤝 Suporte

Para dúvidas ou problemas:
1. Verifique a documentação
2. Consulte os logs do servidor
3. Entre em contato com o desenvolvedor

---

Desenvolvido com ❤️ para barbearias modernas
