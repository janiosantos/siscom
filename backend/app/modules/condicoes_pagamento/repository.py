"""
Repository para Condicoes de Pagamento
"""
from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.condicoes_pagamento.models import CondicaoPagamento, ParcelaPadrao, TipoCondicao
from app.modules.condicoes_pagamento.schemas import (
    CondicaoPagamentoCreate,
    CondicaoPagamentoUpdate,
    ParcelaPadraoCreate,
)


class CondicaoPagamentoRepository:
    """Repository para operações de banco de dados de Condições de Pagamento"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_condicao(self, condicao_data: CondicaoPagamentoCreate) -> CondicaoPagamento:
        """Cria uma nova condição de pagamento (sem parcelas)"""
        data = condicao_data.model_dump(exclude={"parcelas"})
        condicao = CondicaoPagamento(**data)
        self.session.add(condicao)
        await self.session.flush()
        await self.session.refresh(condicao)
        return condicao

    async def create_parcela(
        self, condicao_id: int, parcela_data: ParcelaPadraoCreate
    ) -> ParcelaPadrao:
        """Cria uma parcela padrão"""
        parcela = ParcelaPadrao(
            condicao_id=condicao_id,
            **parcela_data.model_dump()
        )
        self.session.add(parcela)
        await self.session.flush()
        await self.session.refresh(parcela)
        return parcela

    async def get_by_id(self, condicao_id: int) -> Optional[CondicaoPagamento]:
        """Busca condição de pagamento por ID (com parcelas)"""
        result = await self.session.execute(
            select(CondicaoPagamento)
            .options(selectinload(CondicaoPagamento.parcelas))
            .where(CondicaoPagamento.id == condicao_id)
        )
        return result.scalar_one_or_none()

    async def get_by_nome(self, nome: str) -> Optional[CondicaoPagamento]:
        """Busca condição de pagamento por nome"""
        result = await self.session.execute(
            select(CondicaoPagamento).where(CondicaoPagamento.nome == nome)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        apenas_ativas: bool = False,
    ) -> List[CondicaoPagamento]:
        """
        Lista todas as condições de pagamento com paginação e filtros

        Args:
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativas: Se deve listar apenas condições ativas
        """
        query = select(CondicaoPagamento).options(
            selectinload(CondicaoPagamento.parcelas)
        )

        if apenas_ativas:
            query = query.where(CondicaoPagamento.ativa == True)

        query = query.offset(skip).limit(limit).order_by(CondicaoPagamento.nome)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, apenas_ativas: bool = False) -> int:
        """
        Conta total de condições de pagamento

        Args:
            apenas_ativas: Se deve contar apenas condições ativas
        """
        query = select(func.count(CondicaoPagamento.id))

        if apenas_ativas:
            query = query.where(CondicaoPagamento.ativa == True)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_ativas(self) -> List[CondicaoPagamento]:
        """Retorna apenas condições de pagamento ativas"""
        result = await self.session.execute(
            select(CondicaoPagamento)
            .options(selectinload(CondicaoPagamento.parcelas))
            .where(CondicaoPagamento.ativa == True)
            .order_by(CondicaoPagamento.nome)
        )
        return list(result.scalars().all())

    async def get_por_tipo(self, tipo: TipoCondicao) -> List[CondicaoPagamento]:
        """Retorna condições de pagamento por tipo"""
        result = await self.session.execute(
            select(CondicaoPagamento)
            .options(selectinload(CondicaoPagamento.parcelas))
            .where(CondicaoPagamento.tipo == tipo)
            .where(CondicaoPagamento.ativa == True)
            .order_by(CondicaoPagamento.nome)
        )
        return list(result.scalars().all())

    async def get_parcelas_condicao(self, condicao_id: int) -> List[ParcelaPadrao]:
        """Retorna parcelas de uma condição de pagamento"""
        result = await self.session.execute(
            select(ParcelaPadrao)
            .where(ParcelaPadrao.condicao_id == condicao_id)
            .order_by(ParcelaPadrao.numero_parcela)
        )
        return list(result.scalars().all())

    async def update(
        self, condicao_id: int, condicao_data: CondicaoPagamentoUpdate
    ) -> Optional[CondicaoPagamento]:
        """Atualiza uma condição de pagamento"""
        condicao = await self.get_by_id(condicao_id)
        if not condicao:
            return None

        update_data = condicao_data.model_dump(exclude_unset=True, exclude={"parcelas"})
        for field, value in update_data.items():
            setattr(condicao, field, value)

        await self.session.flush()
        await self.session.refresh(condicao)
        return condicao

    async def delete_parcelas_condicao(self, condicao_id: int) -> None:
        """Remove todas as parcelas de uma condição de pagamento"""
        parcelas = await self.get_parcelas_condicao(condicao_id)
        for parcela in parcelas:
            await self.session.delete(parcela)
        await self.session.flush()

    async def delete(self, condicao_id: int) -> bool:
        """Deleta uma condição de pagamento (soft delete - apenas inativa)"""
        condicao = await self.get_by_id(condicao_id)
        if not condicao:
            return False

        condicao.ativa = False
        await self.session.flush()
        return True

    async def search_by_nome(
        self, termo: str, skip: int = 0, limit: int = 100, apenas_ativas: bool = True
    ) -> List[CondicaoPagamento]:
        """
        Busca condições de pagamento por nome ou descrição

        Args:
            termo: Termo de busca
            skip: Quantidade de registros para pular
            limit: Limite de registros
            apenas_ativas: Se deve buscar apenas condições ativas
        """
        query = (
            select(CondicaoPagamento)
            .options(selectinload(CondicaoPagamento.parcelas))
            .where(
                or_(
                    CondicaoPagamento.nome.ilike(f"%{termo}%"),
                    CondicaoPagamento.descricao.ilike(f"%{termo}%"),
                )
            )
        )

        if apenas_ativas:
            query = query.where(CondicaoPagamento.ativa == True)

        query = query.offset(skip).limit(limit).order_by(CondicaoPagamento.nome)
        result = await self.session.execute(query)
        return list(result.scalars().all())
