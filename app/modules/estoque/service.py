"""
Service Layer para Estoque
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.estoque.repository import MovimentacaoEstoqueRepository
from app.modules.estoque.models import TipoMovimentacao
from app.modules.estoque.schemas import (
    EntradaEstoqueCreate,
    SaidaEstoqueCreate,
    AjusteEstoqueCreate,
    MovimentacaoCreate,
    MovimentacaoResponse,
    MovimentacaoList,
    EstoqueAtualResponse,
    TipoMovimentacaoEnum,
)
from app.modules.produtos.repository import ProdutoRepository
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    InsufficientStockException,
    BusinessRuleException,
)


class EstoqueService:
    """Service para regras de negócio de Estoque"""

    def __init__(self, session: AsyncSession):
        self.repository = MovimentacaoEstoqueRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.session = session

    async def validar_produto_existe(self, produto_id: int):
        """
        Valida se o produto existe e está ativo

        Args:
            produto_id: ID do produto

        Raises:
            NotFoundException: Se produto não existe
            ValidationException: Se produto está inativo
        """
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        if not produto.ativo:
            raise ValidationException(
                f"Produto '{produto.descricao}' está inativo e não pode ter movimentações"
            )

        return produto

    async def validar_estoque_suficiente(
        self, produto_id: int, quantidade_necessaria: float
    ) -> bool:
        """
        Verifica se há estoque suficiente para uma saída

        Args:
            produto_id: ID do produto
            quantidade_necessaria: Quantidade necessária

        Returns:
            True se há estoque suficiente

        Raises:
            InsufficientStockException: Se não há estoque suficiente
        """
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        if produto.estoque_atual < quantidade_necessaria:
            raise InsufficientStockException(
                produto=produto.descricao,
                disponivel=produto.estoque_atual,
                necessario=quantidade_necessaria,
            )

        return True

    async def calcular_custo_medio(self, produto_id: int) -> float:
        """
        Calcula o custo médio ponderado de um produto

        O cálculo considera apenas as entradas de estoque para determinar
        o custo médio ponderado do produto.

        Args:
            produto_id: ID do produto

        Returns:
            Custo médio ponderado
        """
        # Busca todas as entradas do produto
        entradas = await self.repository.get_entradas_por_produto(
            produto_id, skip=0, limit=10000
        )

        if not entradas:
            # Se não há entradas, usa o preço de custo do produto
            produto = await self.produto_repository.get_by_id(produto_id)
            return float(produto.preco_custo) if produto else 0.0

        # Calcula custo médio ponderado
        soma_valores = sum(float(e.valor_total) for e in entradas)
        soma_quantidades = sum(float(e.quantidade) for e in entradas)

        if soma_quantidades == 0:
            produto = await self.produto_repository.get_by_id(produto_id)
            return float(produto.preco_custo) if produto else 0.0

        custo_medio = soma_valores / soma_quantidades
        return round(custo_medio, 2)

    async def entrada_estoque(
        self, entrada_data: EntradaEstoqueCreate
    ) -> MovimentacaoResponse:
        """
        Registra uma entrada de estoque e atualiza o estoque atual do produto

        Regras:
        - Produto deve existir e estar ativo
        - Atualiza produto.estoque_atual somando a quantidade
        - Calcula valor_total = quantidade * custo_unitario

        Args:
            entrada_data: Dados da entrada

        Returns:
            MovimentacaoResponse com a movimentação criada
        """
        # Valida produto
        produto = await self.validar_produto_existe(entrada_data.produto_id)

        # Cria movimentação de entrada
        movimentacao_data = MovimentacaoCreate(
            produto_id=entrada_data.produto_id,
            tipo=TipoMovimentacaoEnum.ENTRADA,
            quantidade=entrada_data.quantidade,
            custo_unitario=entrada_data.custo_unitario,
            documento_referencia=entrada_data.documento_referencia,
            observacao=entrada_data.observacao,
            usuario_id=entrada_data.usuario_id,
        )

        movimentacao = await self.repository.create_movimentacao(movimentacao_data)

        # Atualiza estoque atual do produto atomicamente
        produto.estoque_atual = float(produto.estoque_atual) + entrada_data.quantidade

        # Atualiza também o preço de custo se for diferente
        # (considera que a última entrada define o novo preço de custo)
        if entrada_data.custo_unitario > 0:
            produto.preco_custo = entrada_data.custo_unitario

        await self.session.flush()
        await self.session.refresh(movimentacao)

        return MovimentacaoResponse.model_validate(movimentacao)

    async def saida_estoque(
        self, saida_data: SaidaEstoqueCreate
    ) -> MovimentacaoResponse:
        """
        Registra uma saída de estoque e atualiza o estoque atual do produto

        Regras:
        - Produto deve existir e estar ativo
        - Valida se há estoque suficiente antes de permitir saída
        - Atualiza produto.estoque_atual subtraindo a quantidade
        - Se custo_unitario não informado, usa o preço de custo do produto
        - Calcula valor_total = quantidade * custo_unitario

        Args:
            saida_data: Dados da saída

        Returns:
            MovimentacaoResponse com a movimentação criada

        Raises:
            InsufficientStockException: Se não há estoque suficiente
        """
        # Valida produto
        produto = await self.validar_produto_existe(saida_data.produto_id)

        # Valida estoque suficiente
        await self.validar_estoque_suficiente(
            saida_data.produto_id, saida_data.quantidade
        )

        # Define custo unitário (usa preço de custo do produto se não informado)
        custo_unitario = (
            saida_data.custo_unitario
            if saida_data.custo_unitario is not None
            else float(produto.preco_custo)
        )

        # Cria movimentação de saída
        movimentacao_data = MovimentacaoCreate(
            produto_id=saida_data.produto_id,
            tipo=TipoMovimentacaoEnum.SAIDA,
            quantidade=saida_data.quantidade,
            custo_unitario=custo_unitario,
            documento_referencia=saida_data.documento_referencia,
            observacao=saida_data.observacao,
            usuario_id=saida_data.usuario_id,
        )

        movimentacao = await self.repository.create_movimentacao(movimentacao_data)

        # Atualiza estoque atual do produto atomicamente
        produto.estoque_atual = float(produto.estoque_atual) - saida_data.quantidade

        await self.session.flush()
        await self.session.refresh(movimentacao)

        return MovimentacaoResponse.model_validate(movimentacao)

    async def ajuste_estoque(
        self, ajuste_data: AjusteEstoqueCreate
    ) -> MovimentacaoResponse:
        """
        Registra um ajuste manual de estoque

        Regras:
        - Produto deve existir e estar ativo
        - Observação é obrigatória (justificativa do ajuste)
        - Quantidade pode ser positiva (adiciona) ou negativa (remove)
        - Se quantidade negativa, valida se há estoque suficiente
        - Atualiza produto.estoque_atual somando a quantidade (positiva ou negativa)
        - Se custo_unitario não informado, usa o preço de custo do produto

        Args:
            ajuste_data: Dados do ajuste

        Returns:
            MovimentacaoResponse com a movimentação criada

        Raises:
            InsufficientStockException: Se quantidade negativa e não há estoque suficiente
        """
        # Valida produto
        produto = await self.validar_produto_existe(ajuste_data.produto_id)

        # Se quantidade negativa, valida estoque suficiente
        if ajuste_data.quantidade < 0:
            await self.validar_estoque_suficiente(
                ajuste_data.produto_id, abs(ajuste_data.quantidade)
            )

        # Define custo unitário (usa preço de custo do produto se não informado)
        custo_unitario = (
            ajuste_data.custo_unitario
            if ajuste_data.custo_unitario is not None
            else float(produto.preco_custo)
        )

        # Cria movimentação de ajuste
        # Para ajuste, sempre gravamos a quantidade como absoluta
        # mas o tipo AJUSTE indica que é um ajuste
        movimentacao_data = MovimentacaoCreate(
            produto_id=ajuste_data.produto_id,
            tipo=TipoMovimentacaoEnum.AJUSTE,
            quantidade=ajuste_data.quantidade,  # Pode ser positivo ou negativo
            custo_unitario=custo_unitario,
            documento_referencia=None,
            observacao=ajuste_data.observacao,
            usuario_id=ajuste_data.usuario_id,
        )

        movimentacao = await self.repository.create_movimentacao(movimentacao_data)

        # Atualiza estoque atual do produto atomicamente
        # Soma a quantidade (que pode ser positiva ou negativa)
        produto.estoque_atual = float(produto.estoque_atual) + ajuste_data.quantidade

        await self.session.flush()
        await self.session.refresh(movimentacao)

        return MovimentacaoResponse.model_validate(movimentacao)

    async def get_saldo_produto(self, produto_id: int) -> EstoqueAtualResponse:
        """
        Retorna o saldo atual de um produto com informações detalhadas

        Args:
            produto_id: ID do produto

        Returns:
            EstoqueAtualResponse com informações do estoque atual
        """
        # Valida produto
        produto = await self.validar_produto_existe(produto_id)

        # Calcula custo médio
        custo_medio = await self.calcular_custo_medio(produto_id)

        # Calcula valor total do estoque
        valor_total_estoque = float(produto.estoque_atual) * custo_medio

        # Verifica se está abaixo do mínimo
        abaixo_minimo = float(produto.estoque_atual) < float(produto.estoque_minimo)

        return EstoqueAtualResponse(
            produto_id=produto.id,
            produto_descricao=produto.descricao,
            produto_codigo_barras=produto.codigo_barras,
            estoque_atual=float(produto.estoque_atual),
            estoque_minimo=float(produto.estoque_minimo),
            unidade=produto.unidade,
            custo_medio=custo_medio,
            valor_total_estoque=round(valor_total_estoque, 2),
            abaixo_minimo=abaixo_minimo,
        )

    async def get_movimentacao(self, movimentacao_id: int) -> MovimentacaoResponse:
        """Busca movimentação por ID"""
        movimentacao = await self.repository.get_by_id(movimentacao_id)
        if not movimentacao:
            raise NotFoundException(f"Movimentação {movimentacao_id} não encontrada")

        return MovimentacaoResponse.model_validate(movimentacao)

    async def list_movimentacoes(
        self,
        page: int = 1,
        page_size: int = 50,
        produto_id: Optional[int] = None,
        tipo: Optional[TipoMovimentacaoEnum] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> MovimentacaoList:
        """
        Lista movimentações com paginação e filtros

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            produto_id: Filtrar por produto (opcional)
            tipo: Filtrar por tipo de movimentação (opcional)
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            MovimentacaoList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte TipoMovimentacaoEnum para TipoMovimentacao se necessário
        tipo_db = None
        if tipo:
            tipo_db = TipoMovimentacao(tipo.value)

        # Busca movimentações e total
        movimentacoes = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            produto_id=produto_id,
            tipo=tipo_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.repository.count(
            produto_id=produto_id,
            tipo=tipo_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return MovimentacaoList(
            items=[MovimentacaoResponse.model_validate(m) for m in movimentacoes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_movimentacoes_produto(
        self,
        produto_id: int,
        page: int = 1,
        page_size: int = 50,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> MovimentacaoList:
        """
        Lista movimentações de um produto específico

        Args:
            produto_id: ID do produto
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            data_inicio: Data inicial do filtro (opcional)
            data_fim: Data final do filtro (opcional)

        Returns:
            MovimentacaoList com lista paginada
        """
        # Valida produto
        await self.validar_produto_existe(produto_id)

        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca movimentações e total
        movimentacoes = await self.repository.get_by_produto(
            produto_id=produto_id,
            skip=skip,
            limit=page_size,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.repository.count(
            produto_id=produto_id, data_inicio=data_inicio, data_fim=data_fim
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return MovimentacaoList(
            items=[MovimentacaoResponse.model_validate(m) for m in movimentacoes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_relatorio_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        page: int = 1,
        page_size: int = 50,
    ) -> MovimentacaoList:
        """
        Gera relatório de movimentações por período

        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página

        Returns:
            MovimentacaoList com lista paginada de movimentações no período
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca movimentações e total
        movimentacoes = await self.repository.get_movimentacoes_periodo(
            data_inicio=data_inicio, data_fim=data_fim, skip=skip, limit=page_size
        )

        total = await self.repository.count(
            data_inicio=data_inicio, data_fim=data_fim
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return MovimentacaoList(
            items=[MovimentacaoResponse.model_validate(m) for m in movimentacoes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
