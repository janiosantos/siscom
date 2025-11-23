"""
Repository para WMS (Warehouse Management System)
"""
from typing import Optional, List
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.models import LocalizacaoEstoque, ProdutoLocalizacao


class WMSRepository:
    """Repository para operações de WMS"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== LOCALIZAÇÕES ====================

    async def create_localizacao(
        self, codigo: str, descricao: str, tipo: str, **kwargs
    ) -> LocalizacaoEstoque:
        """Cria nova localização de estoque"""
        localizacao = LocalizacaoEstoque(
            codigo=codigo, descricao=descricao, tipo=tipo, **kwargs
        )
        self.session.add(localizacao)
        await self.session.flush()
        await self.session.refresh(localizacao)
        return localizacao

    async def get_localizacao_by_id(
        self, localizacao_id: int
    ) -> Optional[LocalizacaoEstoque]:
        """Busca localização por ID"""
        query = select(LocalizacaoEstoque).where(LocalizacaoEstoque.id == localizacao_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_localizacao_by_codigo(
        self, codigo: str
    ) -> Optional[LocalizacaoEstoque]:
        """Busca localização por código"""
        query = select(LocalizacaoEstoque).where(LocalizacaoEstoque.codigo == codigo)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_localizacoes(
        self, skip: int = 0, limit: int = 50, apenas_ativas: bool = True
    ) -> List[LocalizacaoEstoque]:
        """Lista localizações com paginação"""
        query = select(LocalizacaoEstoque)

        if apenas_ativas:
            query = query.where(LocalizacaoEstoque.ativo == True)

        query = query.order_by(LocalizacaoEstoque.codigo).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_localizacoes(self, apenas_ativas: bool = True) -> int:
        """Conta total de localizações"""
        query = select(func.count(LocalizacaoEstoque.id))

        if apenas_ativas:
            query = query.where(LocalizacaoEstoque.ativo == True)

        result = await self.session.execute(query)
        return result.scalar() or 0

    async def update_localizacao(
        self, localizacao_id: int, **kwargs
    ) -> Optional[LocalizacaoEstoque]:
        """Atualiza uma localização"""
        localizacao = await self.get_localizacao_by_id(localizacao_id)
        if not localizacao:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(localizacao, key):
                setattr(localizacao, key, value)

        await self.session.flush()
        await self.session.refresh(localizacao)
        return localizacao

    async def delete_localizacao(self, localizacao_id: int) -> bool:
        """Inativa uma localização (soft delete)"""
        localizacao = await self.get_localizacao_by_id(localizacao_id)
        if not localizacao:
            return False

        localizacao.ativo = False
        await self.session.flush()
        return True

    # ==================== PRODUTO-LOCALIZAÇÃO ====================

    async def vincular_produto_localizacao(
        self, produto_id: int, localizacao_id: int, quantidade: float = 0, **kwargs
    ) -> ProdutoLocalizacao:
        """Vincula produto a uma localização"""
        vinculo = ProdutoLocalizacao(
            produto_id=produto_id,
            localizacao_id=localizacao_id,
            quantidade=quantidade,
            **kwargs,
        )
        self.session.add(vinculo)
        await self.session.flush()
        await self.session.refresh(vinculo)
        return vinculo

    async def get_produto_localizacao(
        self, produto_id: int, localizacao_id: int
    ) -> Optional[ProdutoLocalizacao]:
        """Busca vínculo produto-localização"""
        query = select(ProdutoLocalizacao).where(
            and_(
                ProdutoLocalizacao.produto_id == produto_id,
                ProdutoLocalizacao.localizacao_id == localizacao_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_localizacoes_produto(
        self, produto_id: int
    ) -> List[ProdutoLocalizacao]:
        """Lista todas as localizações de um produto"""
        query = (
            select(ProdutoLocalizacao)
            .where(ProdutoLocalizacao.produto_id == produto_id)
            .order_by(ProdutoLocalizacao.quantidade.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_produtos_localizacao(
        self, localizacao_id: int
    ) -> List[ProdutoLocalizacao]:
        """Lista todos os produtos de uma localização"""
        query = (
            select(ProdutoLocalizacao)
            .where(ProdutoLocalizacao.localizacao_id == localizacao_id)
            .order_by(ProdutoLocalizacao.quantidade.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def atualizar_quantidade_localizacao(
        self, produto_id: int, localizacao_id: int, nova_quantidade: float
    ) -> Optional[ProdutoLocalizacao]:
        """Atualiza quantidade de produto em uma localização"""
        vinculo = await self.get_produto_localizacao(produto_id, localizacao_id)
        if not vinculo:
            return None

        vinculo.quantidade = nova_quantidade
        await self.session.flush()
        await self.session.refresh(vinculo)
        return vinculo

    async def get_localizacoes_com_produto_disponivel(
        self, produto_id: int, quantidade_necessaria: float
    ) -> List[ProdutoLocalizacao]:
        """
        Busca localizações que possuem o produto com quantidade disponível
        Ordena por FIFO (mais antiga primeiro, baseado em created_at)
        """
        query = (
            select(ProdutoLocalizacao)
            .where(
                and_(
                    ProdutoLocalizacao.produto_id == produto_id,
                    ProdutoLocalizacao.quantidade > 0,
                )
            )
            .order_by(ProdutoLocalizacao.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def buscar_localizacoes_por_tipo(
        self, tipo: str, apenas_ativas: bool = True
    ) -> List[LocalizacaoEstoque]:
        """Busca localizações por tipo"""
        query = select(LocalizacaoEstoque).where(LocalizacaoEstoque.tipo == tipo)

        if apenas_ativas:
            query = query.where(LocalizacaoEstoque.ativo == True)

        query = query.order_by(LocalizacaoEstoque.codigo)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def buscar_por_corredor_prateleira(
        self, corredor: Optional[str] = None, prateleira: Optional[str] = None
    ) -> List[LocalizacaoEstoque]:
        """Busca localizações por corredor e/ou prateleira"""
        query = select(LocalizacaoEstoque).where(LocalizacaoEstoque.ativo == True)

        if corredor:
            query = query.where(LocalizacaoEstoque.corredor == corredor)

        if prateleira:
            query = query.where(LocalizacaoEstoque.prateleira == prateleira)

        query = query.order_by(LocalizacaoEstoque.codigo)
        result = await self.session.execute(query)
        return list(result.scalars().all())
