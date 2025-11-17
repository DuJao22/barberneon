function salvarCarrinhoLocalStorage(carrinho) {
    try {
        localStorage.setItem('carrinho_temp', JSON.stringify(carrinho));
    } catch (e) {
        console.error('Erro ao salvar carrinho:', e);
    }
}

function carregarCarrinhoLocalStorage() {
    try {
        const carrinhoStr = localStorage.getItem('carrinho_temp');
        return carrinhoStr ? JSON.parse(carrinhoStr) : [];
    } catch (e) {
        console.error('Erro ao carregar carrinho:', e);
        return [];
    }
}

function limparCarrinhoLocalStorage() {
    try {
        localStorage.removeItem('carrinho_temp');
    } catch (e) {
        console.error('Erro ao limpar carrinho:', e);
    }
}

function adicionarAoCarrinho(tipo, id, quantidade = 1) {
    fetch('/adicionar-carrinho', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tipo: tipo,
            id: id,
            quantidade: quantidade
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            atualizarBadgeCarrinho(data.count);
            mostrarNotificacao('Item adicionado ao carrinho!');
            
            if (data.carrinho) {
                salvarCarrinhoLocalStorage(data.carrinho);
            }
        }
    })
    .catch(error => console.error('Erro:', error));
}

function alterarQuantidadeCarrinho(tipo, id, quantidade) {
    fetch('/alterar-quantidade-carrinho', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tipo: tipo,
            id: id,
            quantidade: quantidade
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            location.reload();
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => console.error('Erro:', error));
}

function removerDoCarrinho(tipo, id) {
    fetch('/remover-carrinho', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tipo: tipo,
            id: id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            atualizarBadgeCarrinho(data.count);
            location.reload();
        }
    })
    .catch(error => console.error('Erro:', error));
}

function limparCarrinho() {
    if (confirm('Deseja limpar todo o carrinho?')) {
        fetch('/limpar-carrinho', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                limparCarrinhoLocalStorage();
                location.reload();
            }
        })
        .catch(error => console.error('Erro:', error));
    }
}

function restaurarCarrinhoLocalStorage() {
    const carrinho = carregarCarrinhoLocalStorage();
    if (carrinho.length > 0) {
        fetch('/restaurar-carrinho', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ carrinho: carrinho })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                limparCarrinhoLocalStorage();
            }
        })
        .catch(error => console.error('Erro ao restaurar carrinho:', error));
    }
}

function atualizarBadgeCarrinho(count) {
    const badges = document.querySelectorAll('.cart-badge');
    badges.forEach(badge => {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'flex' : 'none';
    });
}

function mostrarNotificacao(mensagem) {
    const notif = document.createElement('div');
    notif.textContent = mensagem;
    notif.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #00D9FF;
        color: #000;
        padding: 16px 24px;
        border-radius: 12px;
        font-weight: 600;
        z-index: 10000;
        box-shadow: 0 4px 20px rgba(0, 217, 255, 0.6);
    `;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = '0';
        notif.style.transition = 'opacity 0.3s ease';
        setTimeout(() => notif.remove(), 300);
    }, 2000);
}

function buscarHorariosDisponiveis() {
    const barbeiroId = document.getElementById('barbeiro').value;
    const data = document.getElementById('data').value;
    
    if (!barbeiroId || !data) return;
    
    fetch('/horarios-disponiveis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            barbeiro_id: barbeiroId,
            data: data
        })
    })
    .then(response => response.json())
    .then(data => {
        const select = document.getElementById('horario');
        select.innerHTML = '<option value="">Selecione um horário</option>';
        
        data.horarios.forEach(horario => {
            const option = document.createElement('option');
            option.value = horario;
            option.textContent = horario;
            select.appendChild(option);
        });
    })
    .catch(error => console.error('Erro:', error));
}

function criarAgendamento(event) {
    event.preventDefault();
    
    const formData = {
        barbeiro_id: document.getElementById('barbeiro').value,
        servico_id: document.getElementById('servico').value,
        data: document.getElementById('data').value,
        horario: document.getElementById('horario').value,
        observacoes: document.getElementById('observacoes').value
    };
    
    fetch('/criar-agendamento', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (response.status === 401) {
            return response.json().then(data => {
                if (data.require_auth) {
                    if (confirm(data.error + '\n\nClique OK para fazer o cadastro ou Cancelar para fazer login.')) {
                        window.location.href = '/cadastro-cliente';
                    } else {
                        window.location.href = '/login-cliente';
                    }
                } else {
                    alert(data.error || 'Você precisa fazer login para agendar');
                    window.location.href = data.redirect || '/login-cliente';
                }
                throw new Error('Não autenticado');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            mostrarNotificacao('Agendamento realizado com sucesso!');
            setTimeout(() => {
                window.location.href = '/perfil';
            }, 1500);
        } else if (data.error) {
            alert(data.error);
        }
    })
    .catch(error => {
        if (error.message !== 'Não autenticado') {
            console.error('Erro:', error);
        }
    });
}

function processarAgendamentoPendente() {
    const urlParams = new URLSearchParams(window.location.search);
    const processarPendente = urlParams.get('processar_agendamento');
    
    if (processarPendente === 'true') {
        fetch('/obter-agendamento-pendente')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.agendamento) {
                const agendamento = data.agendamento;
                
                const barbeiroSelect = document.getElementById('barbeiro');
                const servicoSelect = document.getElementById('servico');
                const dataInput = document.getElementById('data');
                const observacoesInput = document.getElementById('observacoes');
                
                if (barbeiroSelect && agendamento.barbeiro_id) {
                    barbeiroSelect.value = agendamento.barbeiro_id;
                }
                if (servicoSelect && agendamento.servico_id) {
                    servicoSelect.value = agendamento.servico_id;
                }
                if (dataInput && agendamento.data) {
                    dataInput.value = agendamento.data;
                    buscarHorariosDisponiveis();
                    
                    setTimeout(() => {
                        const horarioSelect = document.getElementById('horario');
                        if (horarioSelect && agendamento.horario) {
                            horarioSelect.value = agendamento.horario;
                        }
                    }, 500);
                }
                if (observacoesInput && agendamento.observacoes) {
                    observacoesInput.value = agendamento.observacoes;
                }
                
                mostrarNotificacao('Você pode continuar seu agendamento!');
            }
        })
        .catch(error => console.error('Erro ao processar agendamento pendente:', error));
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    if (sidebar && overlay) {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const dataInput = document.getElementById('data');
    if (dataInput) {
        const hoje = new Date().toISOString().split('T')[0];
        dataInput.setAttribute('min', hoje);
    }
    
    const menuButtons = document.querySelectorAll('.menu-btn');
    menuButtons.forEach(button => {
        if (button.textContent.includes('☰')) {
            button.addEventListener('click', toggleSidebar);
        }
    });
    
    const sidebarClose = document.getElementById('sidebarClose');
    if (sidebarClose) {
        sidebarClose.addEventListener('click', toggleSidebar);
    }
    
    const overlay = document.getElementById('sidebarOverlay');
    if (overlay) {
        overlay.addEventListener('click', toggleSidebar);
    }
    
    processarAgendamentoPendente();
    
    let lastScrollTop = 0;
    const searchBar = document.querySelector('.search-bar');
    const statusBar = document.querySelector('.status-bar');
    
    window.addEventListener('scroll', function() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > 50) {
            if (searchBar) searchBar.classList.add('hide-on-scroll');
            if (statusBar) statusBar.classList.add('hide-on-scroll');
        } else {
            if (searchBar) searchBar.classList.remove('hide-on-scroll');
            if (statusBar) statusBar.classList.remove('hide-on-scroll');
        }
        
        lastScrollTop = scrollTop;
    });
});
