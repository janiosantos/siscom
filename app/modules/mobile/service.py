"""
Service Layer para Mobile - Funcionalidades otimizadas para dispositivos móveis
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.modules.mobile.schemas import (
    ProdutoMobileResponse,
    ClienteMobileResponse,
    VendaMobileCreate,
    OrcamentoMobileCreate,
    EstoqueConsultaResponse,
)
from app.modules.produtos.models import Produto
from app.modules.clientes.models import Cliente
from app.modules.vendas.models import Venda, ItemVenda
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate
from app.modules.orcamentos.service import OrcamentosService
from app.modules.orcamentos.schemas import OrcamentoCreate, ItemOrcamentoCreate
from app.core.exceptions import NotFoundException, ValidationException


class MobileService:
    """Service para funcionalidades mobile otimizadas"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.vendas_service = VendasService(session)
        self.orcamentos_service = OrcamentosService(session)

    async def buscar_produto(
        self, termo: str, limit: int = 20
    ) -> List[ProdutoMobileResponse]:
        """
        Busca produtos por código de barras ou descrição

        Args:
            termo: Termo de busca (código de barras ou parte da descrição)
            limit: Limite de resultados (padrão 20 para mobile)

        Returns:
            Lista de produtos encontrados (versão resumida)
        """
        # Busca por código de barras exato ou descrição parcial
        query = (
            select(Produto)
            .where(
                Produto.ativo == True,
                or_(
                    Produto.codigo_barras.ilike(f"%{termo}%"),
                    Produto.descricao.ilike(f"%{termo}%")
                )
            )
            .order_by(Produto.descricao)
            .limit(limit)
        )

        result = await self.session.execute(query)
        produtos = result.scalars().all()

        return [ProdutoMobileResponse.model_validate(p) for p in produtos]

    async def buscar_produto_por_codigo_barras(
        self, codigo: str
    ) -> Optional[ProdutoMobileResponse]:
        """
        Busca produto por código de barras exato

        Args:
            codigo: Código de barras do produto

        Returns:
            Produto encontrado ou None
        """
        query = select(Produto).where(
            Produto.codigo_barras == codigo,
            Produto.ativo == True
        )

        result = await self.session.execute(query)
        produto = result.scalar_one_or_none()

        if produto:
            return ProdutoMobileResponse.model_validate(produto)
        return None

    async def consultar_estoque(self, produto_id: int) -> EstoqueConsultaResponse:
        """
        Consulta rápida de estoque de um produto

        Args:
            produto_id: ID do produto

        Returns:
            Informações de estoque do produto

        Raises:
            NotFoundException: Se produto não existe
        """
        query = select(Produto).where(Produto.id == produto_id)
        result = await self.session.execute(query)
        produto = result.scalar_one_or_none()

        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Verifica se está abaixo do estoque mínimo
        alerta_estoque_baixo = produto.estoque_atual < produto.estoque_minimo

        return EstoqueConsultaResponse(
            produto_id=produto.id,
            descricao=produto.descricao,
            codigo_barras=produto.codigo_barras,
            estoque_atual=produto.estoque_atual,
            estoque_minimo=produto.estoque_minimo,
            alerta_estoque_baixo=alerta_estoque_baixo,
            preco_venda=produto.preco_venda,
        )

    async def buscar_cliente(
        self, termo: str, limit: int = 20
    ) -> List[ClienteMobileResponse]:
        """
        Busca clientes por nome, CPF/CNPJ ou telefone

        Args:
            termo: Termo de busca
            limit: Limite de resultados (padrão 20 para mobile)

        Returns:
            Lista de clientes encontrados (versão resumida)
        """
        # Busca por nome, CPF/CNPJ, telefone ou celular
        query = (
            select(Cliente)
            .where(
                Cliente.ativo == True,
                or_(
                    Cliente.nome.ilike(f"%{termo}%"),
                    Cliente.cpf_cnpj.ilike(f"%{termo}%"),
                    Cliente.telefone.ilike(f"%{termo}%"),
                    Cliente.celular.ilike(f"%{termo}%")
                )
            )
            .order_by(Cliente.nome)
            .limit(limit)
        )

        result = await self.session.execute(query)
        clientes = result.scalars().all()

        return [ClienteMobileResponse.model_validate(c) for c in clientes]

    async def criar_venda_mobile(self, venda_data: VendaMobileCreate):
        """
        Cria uma venda via mobile (usa VendasService)

        Args:
            venda_data: Dados da venda mobile

        Returns:
            Venda criada

        Raises:
            ValidationException: Se validações falharem
        """
        # Converte schema mobile para schema padrão
        itens_venda = [
            ItemVendaCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                desconto_item=item.desconto_item,
            )
            for item in venda_data.itens
        ]

        venda_create = VendaCreate(
            cliente_id=venda_data.cliente_id,
            vendedor_id=venda_data.vendedor_id,
            forma_pagamento=venda_data.forma_pagamento,
            desconto=venda_data.desconto,
            observacoes=venda_data.observacoes or "Venda criada via Mobile",
            itens=itens_venda,
        )

        # Usa o VendasService que já faz todas as validações
        return await self.vendas_service.criar_venda(venda_create)

    async def criar_orcamento_mobile(self, orcamento_data: OrcamentoMobileCreate):
        """
        Cria um orçamento via mobile (usa OrcamentosService)

        Args:
            orcamento_data: Dados do orçamento mobile

        Returns:
            Orçamento criado

        Raises:
            ValidationException: Se validações falharem
        """
        # Converte schema mobile para schema padrão
        itens_orcamento = [
            ItemOrcamentoCreate(
                produto_id=item.produto_id,
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
                desconto_item=item.desconto_item,
            )
            for item in orcamento_data.itens
        ]

        orcamento_create = OrcamentoCreate(
            cliente_id=orcamento_data.cliente_id,
            vendedor_id=orcamento_data.vendedor_id,
            validade_dias=orcamento_data.validade_dias,
            desconto=orcamento_data.desconto,
            observacoes=orcamento_data.observacoes or "Orçamento criado via Mobile",
            itens=itens_orcamento,
        )

        # Usa o OrcamentosService que já faz todas as validações
        return await self.orcamentos_service.criar_orcamento(orcamento_create)

    async def get_produtos_populares(self, limit: int = 20) -> List[ProdutoMobileResponse]:
        """
        Retorna os produtos mais vendidos dos últimos 30 dias

        Args:
            limit: Quantidade de produtos a retornar (padrão 20)

        Returns:
            Lista dos produtos mais vendidos
        """
        # Data de 30 dias atrás
        data_inicio = datetime.utcnow() - timedelta(days=30)

        # Query para produtos mais vendidos
        # Agrupa por produto_id e soma as quantidades vendidas
        query = (
            select(
                Produto,
                func.sum(ItemVenda.quantidade).label("total_vendido")
            )
            .join(ItemVenda, ItemVenda.produto_id == Produto.id)
            .join(Venda, Venda.id == ItemVenda.venda_id)
            .where(
                Produto.ativo == True,
                Venda.data_venda >= data_inicio
            )
            .group_by(Produto.id)
            .order_by(desc("total_vendido"))
            .limit(limit)
        )

        result = await self.session.execute(query)
        produtos = [row[0] for row in result.all()]

        return [ProdutoMobileResponse.model_validate(p) for p in produtos]

    async def get_clientes_recentes(self, limit: int = 20) -> List[ClienteMobileResponse]:
        """
        Retorna os últimos clientes cadastrados

        Args:
            limit: Quantidade de clientes a retornar (padrão 20)

        Returns:
            Lista dos clientes mais recentes
        """
        query = (
            select(Cliente)
            .where(Cliente.ativo == True)
            .order_by(desc(Cliente.created_at))
            .limit(limit)
        )

        result = await self.session.execute(query)
        clientes = result.scalars().all()

        return [ClienteMobileResponse.model_validate(c) for c in clientes]
