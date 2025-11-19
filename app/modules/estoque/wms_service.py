"""
Service para WMS (Warehouse Management System)
"""
import math
from typing import List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.wms_repository import WMSRepository
from app.modules.estoque.schemas import (
    LocalizacaoEstoqueCreate,
    LocalizacaoEstoqueUpdate,
    LocalizacaoEstoqueResponse,
    LocalizacaoEstoqueList,
    ProdutoLocalizacaoCreate,
    ProdutoLocalizacaoResponse,
    VincularProdutoLocalizacaoRequest,
    PickingListItem,
)
from app.modules.produtos.repository import ProdutoRepository
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)


class WMSService:
    """Service para regras de negócio do WMS"""

    def __init__(self, session: AsyncSession):
        self.repository = WMSRepository(session)
        self.produto_repository = ProdutoRepository(session)

    # ==================== LOCALIZAÇÕES ====================

    async def criar_localizacao(
        self, data: LocalizacaoEstoqueCreate
    ) -> LocalizacaoEstoqueResponse:
        """
        Cria nova localização de estoque

        Regras:
        - Código deve ser único
        - Código é obrigatório
        """
        # Verifica duplicação
        existing = await self.repository.get_localizacao_by_codigo(data.codigo)
        if existing:
            raise DuplicateException(
                f"Localização com código '{data.codigo}' já existe"
            )

        # Cria localização
        localizacao = await self.repository.create_localizacao(
            codigo=data.codigo,
            descricao=data.descricao,
            tipo=data.tipo,
            corredor=data.corredor,
            prateleira=data.prateleira,
            nivel=data.nivel,
            observacoes=data.observacoes,
            ativo=data.ativo,
        )

        return LocalizacaoEstoqueResponse.model_validate(localizacao)

    async def get_localizacao(self, localizacao_id: int) -> LocalizacaoEstoqueResponse:
        """Busca localização por ID"""
        localizacao = await self.repository.get_localizacao_by_id(localizacao_id)
        if not localizacao:
            raise NotFoundException(f"Localização {localizacao_id} não encontrada")

        return LocalizacaoEstoqueResponse.model_validate(localizacao)

    async def list_localizacoes(
        self, page: int = 1, page_size: int = 50, apenas_ativas: bool = True
    ) -> LocalizacaoEstoqueList:
        """Lista localizações com paginação"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        localizacoes = await self.repository.list_localizacoes(
            skip, page_size, apenas_ativas
        )
        total = await self.repository.count_localizacoes(apenas_ativas)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return LocalizacaoEstoqueList(
            items=[
                LocalizacaoEstoqueResponse.model_validate(loc) for loc in localizacoes
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_localizacao(
        self, localizacao_id: int, data: LocalizacaoEstoqueUpdate
    ) -> LocalizacaoEstoqueResponse:
        """Atualiza uma localização"""
        # Verifica se existe
        localizacao_atual = await self.repository.get_localizacao_by_id(localizacao_id)
        if not localizacao_atual:
            raise NotFoundException(f"Localização {localizacao_id} não encontrada")

        # Atualiza
        update_data = data.model_dump(exclude_unset=True)
        localizacao = await self.repository.update_localizacao(
            localizacao_id, **update_data
        )

        return LocalizacaoEstoqueResponse.model_validate(localizacao)

    async def inativar_localizacao(self, localizacao_id: int) -> bool:
        """Inativa uma localização (soft delete)"""
        localizacao = await self.repository.get_localizacao_by_id(localizacao_id)
        if not localizacao:
            raise NotFoundException(f"Localização {localizacao_id} não encontrada")

        return await self.repository.delete_localizacao(localizacao_id)

    # ==================== PRODUTO-LOCALIZAÇÃO ====================

    async def vincular_produto_localizacao(
        self, produto_id: int, data: VincularProdutoLocalizacaoRequest
    ) -> ProdutoLocalizacaoResponse:
        """
        Vincula produto a uma localização

        Regras:
        - Produto deve existir
        - Localização deve existir
        - Não pode duplicar vínculo
        """
        # Verifica produto
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        # Verifica localização
        localizacao = await self.repository.get_localizacao_by_id(data.localizacao_id)
        if not localizacao:
            raise NotFoundException(
                f"Localização {data.localizacao_id} não encontrada"
            )

        # Verifica duplicação
        existing = await self.repository.get_produto_localizacao(
            produto_id, data.localizacao_id
        )
        if existing:
            raise DuplicateException(
                f"Produto {produto_id} já vinculado à localização {data.localizacao_id}"
            )

        # Vincula
        vinculo = await self.repository.vincular_produto_localizacao(
            produto_id=produto_id,
            localizacao_id=data.localizacao_id,
            quantidade=data.quantidade,
            quantidade_minima=data.quantidade_minima,
            quantidade_maxima=data.quantidade_maxima,
        )

        return ProdutoLocalizacaoResponse.model_validate(vinculo)

    async def get_localizacoes_produto(
        self, produto_id: int
    ) -> List[ProdutoLocalizacaoResponse]:
        """Lista todas as localizações onde um produto está armazenado"""
        produto = await self.produto_repository.get_by_id(produto_id)
        if not produto:
            raise NotFoundException(f"Produto {produto_id} não encontrado")

        vinculos = await self.repository.list_localizacoes_produto(produto_id)

        return [ProdutoLocalizacaoResponse.model_validate(v) for v in vinculos]

    async def atualizar_quantidade_localizacao(
        self, produto_id: int, localizacao_id: int, nova_quantidade: float
    ) -> ProdutoLocalizacaoResponse:
        """Atualiza quantidade de produto em uma localização"""
        vinculo = await self.repository.atualizar_quantidade_localizacao(
            produto_id, localizacao_id, nova_quantidade
        )

        if not vinculo:
            raise NotFoundException(
                f"Vínculo produto {produto_id} - localização {localizacao_id} não encontrado"
            )

        return ProdutoLocalizacaoResponse.model_validate(vinculo)

    # ==================== PICKING (SEPARAÇÃO) ====================

    async def gerar_lista_picking(
        self, itens_pedido: List[Dict[str, Any]]
    ) -> List[PickingListItem]:
        """
        Gera lista de separação (picking) para um pedido

        Args:
            itens_pedido: Lista de dicts com 'produto_id' e 'quantidade'

        Returns:
            Lista de itens para picking com localização sugerida (FIFO)

        Regras:
        - Sugere localizações por ordem FIFO (mais antiga primeiro)
        - Verifica disponibilidade em cada localização
        - Pode sugerir múltiplas localizações se necessário
        """
        lista_picking = []

        for item in itens_pedido:
            produto_id = item["produto_id"]
            quantidade_necessaria = item["quantidade"]

            # Busca produto
            produto = await self.produto_repository.get_by_id(produto_id)
            if not produto:
                continue

            # Busca localizações com produto disponível (FIFO)
            localizacoes = await self.repository.get_localizacoes_com_produto_disponivel(
                produto_id, quantidade_necessaria
            )

            quantidade_restante = quantidade_necessaria

            for vinculo in localizacoes:
                if quantidade_restante <= 0:
                    break

                quantidade_a_pegar = min(vinculo.quantidade, quantidade_restante)

                picking_item = PickingListItem(
                    produto_id=produto_id,
                    produto_descricao=produto.descricao,
                    codigo_barras=produto.codigo_barras,
                    quantidade_necessaria=quantidade_a_pegar,
                    localizacao_codigo=vinculo.localizacao.codigo,
                    localizacao_descricao=vinculo.localizacao.descricao,
                    localizacao_tipo=vinculo.localizacao.tipo,
                    quantidade_disponivel=vinculo.quantidade,
                )

                lista_picking.append(picking_item)
                quantidade_restante -= quantidade_a_pegar

        return lista_picking

    async def buscar_por_tipo(
        self, tipo: str, apenas_ativas: bool = True
    ) -> List[LocalizacaoEstoqueResponse]:
        """Busca localizações por tipo"""
        localizacoes = await self.repository.buscar_localizacoes_por_tipo(
            tipo, apenas_ativas
        )
        return [LocalizacaoEstoqueResponse.model_validate(loc) for loc in localizacoes]

    async def buscar_por_corredor_prateleira(
        self, corredor: str = None, prateleira: str = None
    ) -> List[LocalizacaoEstoqueResponse]:
        """Busca localizações por corredor e/ou prateleira"""
        localizacoes = await self.repository.buscar_por_corredor_prateleira(
            corredor, prateleira
        )
        return [LocalizacaoEstoqueResponse.model_validate(loc) for loc in localizacoes]
