"""
Service Layer para Orçamentos
"""
from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.orcamentos.repository import OrcamentoRepository
from app.modules.orcamentos.models import StatusOrcamento
from app.modules.orcamentos.schemas import (
    OrcamentoCreate,
    OrcamentoUpdate,
    OrcamentoResponse,
    OrcamentoList,
    ItemOrcamentoCreate,
    ItemOrcamentoResponse,
    StatusOrcamentoEnum,
    ConverterOrcamentoRequest,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class OrcamentosService:
    """Service para regras de negócio de Orçamentos"""

    def __init__(self, session: AsyncSession):
        self.repository = OrcamentoRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.session = session

    async def criar_orcamento(self, orcamento_data: OrcamentoCreate) -> OrcamentoResponse:
        """
        Cria um orçamento completo com itens

        Regras:
        - Valida se todos os produtos existem
        - Calcula data_validade (data_orcamento + validade_dias)
        - Calcula totais (subtotal, desconto, valor_total)
        - NÃO mexe em estoque (orçamento é apenas informacional)
        - Cria o orçamento com status ABERTO

        Args:
            orcamento_data: Dados do orçamento com itens

        Returns:
            OrcamentoResponse com o orçamento criado

        Raises:
            NotFoundException: Se produto não existe
            ValidationException: Se validações falharem
        """
        # Valida que há itens
        if not orcamento_data.itens or len(orcamento_data.itens) == 0:
            raise ValidationException("Orçamento deve ter pelo menos um item")

        # Valida produtos para todos os itens
        for item in orcamento_data.itens:
            # Verifica se produto existe
            produto = await self.produto_repository.get_by_id(item.produto_id)
            if not produto:
                raise NotFoundException(f"Produto {item.produto_id} não encontrado")

            if not produto.ativo:
                raise ValidationException(
                    f"Produto '{produto.descricao}' está inativo e não pode ser orçado"
                )

        # Cria o orçamento (sem itens)
        orcamento = await self.repository.create_orcamento(orcamento_data)

        # Calcula subtotal do orçamento
        subtotal = 0.0

        # Cria itens (SEM registrar movimentação de estoque)
        for item_data in orcamento_data.itens:
            # Calcula subtotal do item
            subtotal_item = item_data.quantidade * item_data.preco_unitario

            # Calcula total do item (subtotal - desconto)
            total_item = subtotal_item - item_data.desconto_item

            # Cria item do orçamento
            await self.repository.create_item_orcamento(
                orcamento_id=orcamento.id,
                item_data=item_data,
                total=total_item,
            )

            # Acumula subtotal do orçamento
            subtotal += subtotal_item

        # Calcula valor total do orçamento (subtotal - desconto)
        valor_total = subtotal - orcamento_data.desconto

        # Valida que valor total não seja negativo
        if valor_total < 0:
            raise ValidationException(
                "Desconto não pode ser maior que o subtotal do orçamento"
            )

        # Atualiza totais do orçamento
        await self.repository.atualizar_totais_orcamento(
            orcamento_id=orcamento.id,
            subtotal=subtotal,
            desconto=orcamento_data.desconto,
            valor_total=valor_total,
        )

        # Commit da transação
        await self.session.flush()

        # Busca orçamento completo com itens
        orcamento_completo = await self.repository.get_by_id(orcamento.id)

        return OrcamentoResponse.model_validate(orcamento_completo)

    async def atualizar_orcamento(
        self, orcamento_id: int, orcamento_data: OrcamentoUpdate
    ) -> OrcamentoResponse:
        """
        Atualiza um orçamento

        Regras:
        - Orçamento deve existir
        - Só pode editar se status = ABERTO
        - Recalcula data_validade se validade_dias for alterado
        - Recalcula valor_total se desconto for alterado

        Args:
            orcamento_id: ID do orçamento
            orcamento_data: Dados para atualização

        Returns:
            OrcamentoResponse com o orçamento atualizado

        Raises:
            NotFoundException: Se orçamento não existe
            BusinessRuleException: Se orçamento não pode ser editado
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        if orcamento.status != StatusOrcamento.ABERTO:
            raise BusinessRuleException(
                f"Orçamento não pode ser editado. Status atual: {orcamento.status}. "
                "Apenas orçamentos com status ABERTO podem ser editados."
            )

        # Atualiza orçamento
        orcamento_atualizado = await self.repository.atualizar_orcamento(
            orcamento_id=orcamento_id,
            cliente_id=orcamento_data.cliente_id,
            validade_dias=orcamento_data.validade_dias,
            desconto=orcamento_data.desconto,
            observacoes=orcamento_data.observacoes,
        )

        await self.session.flush()

        return OrcamentoResponse.model_validate(orcamento_atualizado)

    async def aprovar_orcamento(self, orcamento_id: int) -> OrcamentoResponse:
        """
        Aprova um orçamento (altera status para APROVADO)

        Regras:
        - Orçamento deve existir
        - Orçamento deve estar ABERTO
        - Altera status para APROVADO

        Args:
            orcamento_id: ID do orçamento

        Returns:
            OrcamentoResponse com o orçamento aprovado

        Raises:
            NotFoundException: Se orçamento não existe
            BusinessRuleException: Se orçamento não pode ser aprovado
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        if orcamento.status != StatusOrcamento.ABERTO:
            raise BusinessRuleException(
                f"Orçamento não pode ser aprovado. Status atual: {orcamento.status}. "
                "Apenas orçamentos com status ABERTO podem ser aprovados."
            )

        # Aprova orçamento
        orcamento_aprovado = await self.repository.atualizar_status(
            orcamento_id, StatusOrcamento.APROVADO
        )

        await self.session.flush()

        return OrcamentoResponse.model_validate(orcamento_aprovado)

    async def reprovar_orcamento(self, orcamento_id: int) -> OrcamentoResponse:
        """
        Reprova um orçamento (altera status para PERDIDO)

        Regras:
        - Orçamento deve existir
        - Orçamento deve estar ABERTO ou APROVADO
        - Altera status para PERDIDO

        Args:
            orcamento_id: ID do orçamento

        Returns:
            OrcamentoResponse com o orçamento reprovado

        Raises:
            NotFoundException: Se orçamento não existe
            BusinessRuleException: Se orçamento não pode ser reprovado
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        if orcamento.status not in [StatusOrcamento.ABERTO, StatusOrcamento.APROVADO]:
            raise BusinessRuleException(
                f"Orçamento não pode ser reprovado. Status atual: {orcamento.status}. "
                "Apenas orçamentos com status ABERTO ou APROVADO podem ser reprovados."
            )

        # Reprova orçamento
        orcamento_reprovado = await self.repository.atualizar_status(
            orcamento_id, StatusOrcamento.PERDIDO
        )

        await self.session.flush()

        return OrcamentoResponse.model_validate(orcamento_reprovado)

    async def converter_para_venda(
        self, orcamento_id: int, converter_data: ConverterOrcamentoRequest
    ) -> dict:
        """
        Converte um orçamento para venda

        Regras:
        - Orçamento deve existir
        - Orçamento deve estar APROVADO
        - Valida estoque disponível para todos os itens
        - Cria venda através de VendasService
        - Atualiza status do orçamento para CONVERTIDO
        - Venda criada já registra saída de estoque automaticamente

        Args:
            orcamento_id: ID do orçamento
            converter_data: Dados para conversão (forma_pagamento)

        Returns:
            Dict com orçamento e venda criada

        Raises:
            NotFoundException: Se orçamento não existe
            BusinessRuleException: Se orçamento não pode ser convertido
            InsufficientStockException: Se não há estoque suficiente
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        if orcamento.status != StatusOrcamento.APROVADO:
            raise BusinessRuleException(
                f"Orçamento não pode ser convertido para venda. Status atual: {orcamento.status}. "
                "Apenas orçamentos com status APROVADO podem ser convertidos."
            )

        # Prepara dados da venda a partir do orçamento
        itens_venda = []
        for item in orcamento.itens:
            item_venda = ItemVendaCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                desconto_item=item.desconto_item,
            )
            itens_venda.append(item_venda)

        venda_data = VendaCreate(
            cliente_id=orcamento.cliente_id,
            vendedor_id=orcamento.vendedor_id,
            forma_pagamento=converter_data.forma_pagamento,
            desconto=orcamento.desconto,
            observacoes=f"Convertido do Orçamento #{orcamento.id}",
            itens=itens_venda,
        )

        # Cria venda através do VendasService
        # O VendasService já faz todas as validações e movimentações de estoque
        vendas_service = VendasService(self.session)
        venda = await vendas_service.criar_venda(venda_data)

        # Atualiza status do orçamento para CONVERTIDO
        await self.repository.atualizar_status(orcamento_id, StatusOrcamento.CONVERTIDO)

        await self.session.flush()

        # Busca orçamento atualizado
        orcamento_atualizado = await self.repository.get_by_id(orcamento_id)

        return {
            "orcamento": OrcamentoResponse.model_validate(orcamento_atualizado),
            "venda": venda,
        }

    async def converter_para_os(self, orcamento_id: int) -> OrcamentoResponse:
        """
        Converte um orçamento para ordem de serviço (OS)

        NOTA: Preparado para futura integração com módulo de OS (Sprint 4)

        Args:
            orcamento_id: ID do orçamento

        Returns:
            OrcamentoResponse

        Raises:
            NotImplementedError: Funcionalidade ainda não implementada
        """
        raise NotImplementedError(
            "Conversão para Ordem de Serviço será implementada na Sprint 4"
        )

    async def get_orcamento(self, orcamento_id: int) -> OrcamentoResponse:
        """
        Busca orçamento completo com itens

        Args:
            orcamento_id: ID do orçamento

        Returns:
            OrcamentoResponse com o orçamento completo

        Raises:
            NotFoundException: Se orçamento não existe
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        return OrcamentoResponse.model_validate(orcamento)

    async def list_orcamentos(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[StatusOrcamentoEnum] = None,
        cliente_id: Optional[int] = None,
        vendedor_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> OrcamentoList:
        """
        Lista orçamentos com paginação e filtros

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            status: Filtrar por status (opcional)
            cliente_id: Filtrar por cliente (opcional)
            vendedor_id: Filtrar por vendedor (opcional)
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            OrcamentoList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte StatusOrcamentoEnum para StatusOrcamento se necessário
        status_db = None
        if status:
            status_db = StatusOrcamento(status.value)

        # Busca orçamentos e total
        orcamentos = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            status=status_db,
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.repository.count(
            status=status_db,
            cliente_id=cliente_id,
            vendedor_id=vendedor_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrcamentoList(
            items=[OrcamentoResponse.model_validate(o) for o in orcamentos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_orcamentos_vencidos(
        self, page: int = 1, page_size: int = 50
    ) -> OrcamentoList:
        """
        Busca orçamentos vencidos

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página

        Returns:
            OrcamentoList com orçamentos vencidos
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        orcamentos = await self.repository.get_orcamentos_vencidos(
            skip=skip, limit=page_size
        )

        # Conta total de orçamentos vencidos
        hoje = date.today()
        total = await self.repository.count(
            status=StatusOrcamento.ABERTO,
            data_fim=datetime.combine(hoje, datetime.min.time()),
        )

        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrcamentoList(
            items=[OrcamentoResponse.model_validate(o) for o in orcamentos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_orcamentos_a_vencer(
        self, dias: int = 7, page: int = 1, page_size: int = 50
    ) -> OrcamentoList:
        """
        Busca orçamentos a vencer nos próximos N dias

        Args:
            dias: Quantidade de dias à frente para verificar
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página

        Returns:
            OrcamentoList com orçamentos a vencer
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        orcamentos = await self.repository.get_orcamentos_a_vencer(
            dias=dias, skip=skip, limit=page_size
        )

        # Aproximação do total (não conta exatamente, mas serve para paginação)
        total = len(orcamentos)
        if len(orcamentos) == page_size:
            total = page * page_size + 1  # Indica que pode haver mais páginas

        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrcamentoList(
            items=[OrcamentoResponse.model_validate(o) for o in orcamentos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def deletar_orcamento(self, orcamento_id: int) -> OrcamentoResponse:
        """
        Deleta (cancela) um orçamento

        Regras:
        - Orçamento deve existir
        - Orçamento deve estar ABERTO
        - Deleta o orçamento e seus itens (cascade)

        Args:
            orcamento_id: ID do orçamento

        Returns:
            OrcamentoResponse com o orçamento deletado

        Raises:
            NotFoundException: Se orçamento não existe
            BusinessRuleException: Se orçamento não pode ser deletado
        """
        orcamento = await self.repository.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        if orcamento.status != StatusOrcamento.ABERTO:
            raise BusinessRuleException(
                f"Orçamento não pode ser deletado. Status atual: {orcamento.status}. "
                "Apenas orçamentos com status ABERTO podem ser deletados."
            )

        # Salva dados do orçamento para retorno
        orcamento_response = OrcamentoResponse.model_validate(orcamento)

        # Deleta orçamento
        await self.repository.deletar_orcamento(orcamento_id)

        await self.session.flush()

        return orcamento_response
