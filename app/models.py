"""
Central module importing all models for SQLAlchemy metadata

This ensures all models are registered with Base.metadata before
calling create_all() in tests and migrations.
"""

# Core models
from app.modules.auth.models import (  # noqa: F401
    User,
    Role,
    Permission,
    AuditLog,
    RefreshToken,
    user_roles,
    role_permissions,
)

# Sprint 1 - Base
from app.modules.produtos.models import Produto  # noqa: F401
from app.modules.categorias.models import Categoria  # noqa: F401
from app.modules.estoque.models import (  # noqa: F401
    MovimentacaoEstoque,
    Lote,
    NumeroSerie,
    EnderecoEstoque,
    InventarioRotativo,
)
from app.modules.vendas.models import Venda, ItemVenda  # noqa: F401
from app.modules.pdv.models import Caixa, MovimentacaoCaixa  # noqa: F401
from app.modules.financeiro.models import (  # noqa: F401
    ContaPagar,
    ContaReceber,
    Baixa,
)
from app.modules.nfe.models import NotaFiscal, ItemNotaFiscal  # noqa: F401
from app.modules.clientes.models import Cliente  # noqa: F401
from app.modules.condicoes_pagamento.models import (  # noqa: F401
    CondicaoPagamento,
    ParcelaCondicao,
)

# Sprint 2
from app.modules.orcamentos.models import (  # noqa: F401
    Orcamento,
    ItemOrcamento,
)

# Sprint 3
from app.modules.compras.models import (  # noqa: F401
    PedidoCompra,
    ItemPedidoCompra,
)
from app.modules.fornecedores.models import (  # noqa: F401
    Fornecedor,
    AvaliacaoFornecedor,
)

# Sprint 4
from app.modules.os.models import (  # noqa: F401
    OrdemServico,
    ItemOS,
    Tecnico,
)

# Sprint 6
from app.modules.ecommerce.models import (  # noqa: F401
    PedidoEcommerce,
    ItemPedidoEcommerce,
    CarrinhoEcommerce,
    ItemCarrinho,
)
from app.modules.relatorios.models import (  # noqa: F401
    RelatorioAgendado,
    HistoricoRelatorio,
)

# Sprint 7
from app.modules.crm.models import (  # noqa: F401
    Contato,
    Interacao,
    Tarefa,
)

# Pagamentos (Fase 2)
from app.modules.pagamentos.models import (  # noqa: F401
    ChavePix,
    TransacaoPix,
    Boleto,
    ConciliacaoBancaria,
)

# Import/Export (Fase 3)
try:
    from app.modules.importexport.models import (  # noqa: F401
        ImportJob,
        ExportJob,
    )
except ImportError:
    pass

# LGPD (Fase 2)
try:
    from app.modules.lgpd.models import (  # noqa: F401
        ConsentimentoLGPD,
        SolicitacaoExclusao,
    )
except ImportError:
    pass

# Multi-tenant (Fase 3)
try:
    from app.modules.multiempresa.models import Empresa  # noqa: F401
except ImportError:
    pass

__all__ = [
    # Auth
    "User",
    "Role",
    "Permission",
    "AuditLog",
    "RefreshToken",
    # Sprint 1
    "Produto",
    "Categoria",
    "MovimentacaoEstoque",
    "Lote",
    "NumeroSerie",
    "EnderecoEstoque",
    "InventarioRotativo",
    "Venda",
    "ItemVenda",
    "Caixa",
    "MovimentacaoCaixa",
    "ContaPagar",
    "ContaReceber",
    "Baixa",
    "NotaFiscal",
    "ItemNotaFiscal",
    "Cliente",
    "CondicaoPagamento",
    "ParcelaCondicao",
    # Sprint 2
    "Orcamento",
    "ItemOrcamento",
    # Sprint 3
    "PedidoCompra",
    "ItemPedidoCompra",
    "Fornecedor",
    "AvaliacaoFornecedor",
    # Sprint 4
    "OrdemServico",
    "ItemOS",
    "Tecnico",
    # Sprint 6
    "PedidoEcommerce",
    "ItemPedidoEcommerce",
    "CarrinhoEcommerce",
    "ItemCarrinho",
    "RelatorioAgendado",
    "HistoricoRelatorio",
    # Sprint 7
    "Contato",
    "Interacao",
    "Tarefa",
    # Pagamentos
    "ChavePix",
    "TransacaoPix",
    "Boleto",
    "ConciliacaoBancaria",
]
