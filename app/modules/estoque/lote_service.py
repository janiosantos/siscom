"""
Service Layer para Lotes de Estoque
"""
from typing import Optional, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.estoque.lote_repository import LoteEstoqueRepository
from app.modules.estoque.schemas import (
    LoteEstoqueCreate,
    LoteEstoqueResponse,
    LoteEstoqueList,
    ProdutoLoteFIFO,
)
from app.modules.produtos.repository import ProdutoRepository
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    InsufficientStockException,
    BusinessRuleException,
)


class LoteEstoqueService:
    """Service para regras de negócio de Lotes de Estoque"""

    def __init__(self, session: AsyncSession):
        self.repository = LoteEstoqueRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.session = session

    async def validar_produto_controla_lote(self, produto_id: int) -> bool:
        """
        Verifica se o produto tem controle de lote habilitado

        Args:
            produto_id: ID do produto

        Returns:
            True se produto controla lote

        Raises:
            NotFoundException: Se produto não existe
            BusinessRuleException: Se produto não controla lote
        """
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        if not produto.controla_lote:
            raise BusinessRuleException(
                f"Produto '{produto.descricao}' não possui controle de lote habilitado"
            )

        return True

    async def criar_lote(self, lote_data: LoteEstoqueCreate) -> LoteEstoqueResponse:
        """
        Cria um novo lote de estoque

        Regras:
        - Produto deve existir e ter controla_lote=True
        - Data de validade deve ser futura
        - Número do lote é obrigatório

        Args:
            lote_data: Dados do lote

        Returns:
            LoteEstoqueResponse com o lote criado
        """
        # Valida se produto controla lote
        await self.validar_produto_controla_lote(lote_data.produto_id)

        # Cria o lote
        lote = await self.repository.create_lote(lote_data)
        await self.session.refresh(lote)

        return LoteEstoqueResponse.model_validate(lote)

    async def get_lote(self, lote_id: int) -> LoteEstoqueResponse:
        """
        Busca lote por ID

        Args:
            lote_id: ID do lote

        Returns:
            LoteEstoqueResponse

        Raises:
            NotFoundException: Se lote não encontrado
        """
        lote = await self.repository.get_by_id(lote_id)
        if not lote:
            raise NotFoundException(f"Lote {lote_id} não encontrado")

        return LoteEstoqueResponse.model_validate(lote)

    async def listar_lotes_produto(
        self,
        produto_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> LoteEstoqueList:
        """
        Lista todos os lotes de um produto

        Args:
            produto_id: ID do produto
            page: Página atual
            page_size: Tamanho da página

        Returns:
            LoteEstoqueList com lista paginada
        """
        # Valida produto
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca lotes
        lotes = await self.repository.get_by_produto(
            produto_id=produto_id,
            skip=skip,
            limit=page_size,
        )

        # Conta total
        total = await self.repository.count_by_produto(produto_id)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return LoteEstoqueList(
            items=[LoteEstoqueResponse.model_validate(l) for l in lotes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def sugerir_lote_fifo(self, produto_id: int) -> Optional[ProdutoLoteFIFO]:
        """
        Retorna o lote mais antigo disponível para saída (FIFO)
        Prioriza pela data de validade mais próxima

        Args:
            produto_id: ID do produto

        Returns:
            ProdutoLoteFIFO com sugestão de lote ou None se não houver lote disponível
        """
        # Valida produto
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Busca lote mais antigo disponível
        lote = await self.repository.get_lote_mais_antigo_disponivel(produto_id)

        if not lote:
            return None

        # Calcula dias para vencer
        hoje = date.today()
        dias_para_vencer = (lote.data_validade - hoje).days

        # Verifica se está vencido
        esta_vencido = lote.data_validade < hoje

        return ProdutoLoteFIFO(
            lote_id=lote.id,
            numero_lote=lote.numero_lote,
            data_validade=lote.data_validade,
            quantidade_disponivel=float(lote.quantidade_atual),
            custo_unitario=float(lote.custo_unitario),
            esta_vencido=esta_vencido,
            dias_para_vencer=dias_para_vencer,
        )

    async def get_lotes_vencidos(
        self,
        page: int = 1,
        page_size: int = 50,
    ) -> LoteEstoqueList:
        """
        Lista lotes vencidos

        Args:
            page: Página atual
            page_size: Tamanho da página

        Returns:
            LoteEstoqueList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca lotes vencidos
        lotes = await self.repository.get_lotes_vencidos(
            skip=skip,
            limit=page_size,
        )

        # Para simplificar, vamos contar apenas os retornados
        # Em produção, você poderia fazer um count específico
        total = len(lotes)
        pages = math.ceil(total / page_size) if total > 0 else 1

        return LoteEstoqueList(
            items=[LoteEstoqueResponse.model_validate(l) for l in lotes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_lotes_a_vencer(
        self,
        dias: int = 30,
        page: int = 1,
        page_size: int = 50,
    ) -> LoteEstoqueList:
        """
        Lista lotes que vencem nos próximos N dias

        Args:
            dias: Número de dias para verificar
            page: Página atual
            page_size: Tamanho da página

        Returns:
            LoteEstoqueList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca lotes a vencer
        lotes = await self.repository.get_lotes_a_vencer(
            dias=dias,
            skip=skip,
            limit=page_size,
        )

        # Para simplificar, vamos contar apenas os retornados
        total = len(lotes)
        pages = math.ceil(total / page_size) if total > 0 else 1

        return LoteEstoqueList(
            items=[LoteEstoqueResponse.model_validate(l) for l in lotes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def dar_baixa_lote(
        self, lote_id: int, quantidade: float
    ) -> LoteEstoqueResponse:
        """
        Dá baixa em um lote, reduzindo a quantidade_atual

        Regras:
        - Lote deve existir
        - Quantidade deve ser positiva
        - Deve haver estoque suficiente no lote

        Args:
            lote_id: ID do lote
            quantidade: Quantidade a dar baixa

        Returns:
            LoteEstoqueResponse com lote atualizado

        Raises:
            NotFoundException: Se lote não encontrado
            InsufficientStockException: Se quantidade insuficiente no lote
        """
        # Busca lote
        lote = await self.repository.get_by_id(lote_id)
        if not lote:
            raise NotFoundException(f"Lote {lote_id} não encontrado")

        # Valida quantidade disponível
        if float(lote.quantidade_atual) < quantidade:
            raise InsufficientStockException(
                produto=f"Lote {lote.numero_lote}",
                disponivel=float(lote.quantidade_atual),
                necessario=quantidade,
            )

        # Dá baixa no lote
        lote_atualizado = await self.repository.dar_baixa_lote(lote_id, quantidade)
        await self.session.refresh(lote_atualizado)

        return LoteEstoqueResponse.model_validate(lote_atualizado)

    async def calcular_estoque_por_lote(self, produto_id: int) -> float:
        """
        Calcula o estoque total de um produto somando todos os lotes

        Args:
            produto_id: ID do produto

        Returns:
            Estoque total (soma de quantidade_atual de todos os lotes)
        """
        # Valida produto
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Calcula estoque total por lote
        estoque_total = await self.repository.get_estoque_total_por_produto(produto_id)

        return estoque_total
