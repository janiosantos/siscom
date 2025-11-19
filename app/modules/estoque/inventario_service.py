"""
Service para Inventário de Estoque
"""
import math
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.estoque.inventario_repository import InventarioRepository
from app.modules.estoque.wms_repository import WMSRepository
from app.modules.estoque.repository import EstoqueRepository
from app.modules.produtos.repository import ProdutoRepository
from app.modules.categorias.repository import CategoriaRepository
from app.modules.estoque.models import StatusInventario
from app.modules.estoque.schemas import (
    FichaInventarioCreate,
    FichaInventarioResponse,
    FichaInventarioList,
    ItemInventarioResponse,
    RegistrarContagemRequest,
    IniciarContagemRequest,
    FinalizarContagemRequest,
    AcuracidadeResponse,
    DivergenciaItem,
)
from app.core.exceptions import NotFoundException, ValidationException


class InventarioService:
    """Service para regras de negócio de Inventário"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = InventarioRepository(session)
        self.wms_repository = WMSRepository(session)
        self.estoque_repository = EstoqueRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.categoria_repository = CategoriaRepository(session)

    # ==================== FICHAS DE INVENTÁRIO ====================

    async def criar_ficha_inventario(
        self, data: FichaInventarioCreate
    ) -> FichaInventarioResponse:
        """
        Cria nova ficha de inventário e gera itens automaticamente

        Regras:
        - GERAL: Inclui todos os produtos ativos
        - PARCIAL: Apenas produtos/localizações/categorias especificadas
        - ROTATIVO: Produtos da curva A/B com maior rotatividade
        """
        # Cria ficha
        ficha = await self.repository.create_ficha(
            tipo=data.tipo,
            usuario_responsavel_id=data.usuario_responsavel_id,
            observacoes=data.observacoes,
        )

        # Gera itens automaticamente
        await self._gerar_itens_inventario(ficha.id, data)

        # Recarrega ficha com itens
        ficha = await self.repository.get_ficha_by_id(ficha.id)
        return FichaInventarioResponse.model_validate(ficha)

    async def _gerar_itens_inventario(
        self, ficha_id: int, data: FichaInventarioCreate
    ):
        """Gera itens de inventário baseado no tipo e filtros"""
        if data.tipo == "GERAL":
            # Inventário geral: todos os produtos ativos
            produtos = await self.produto_repository.get_all(0, 10000, apenas_ativos=True)
            for produto in produtos:
                await self.repository.create_item(
                    ficha_id=ficha_id,
                    produto_id=produto.id,
                    quantidade_sistema=float(produto.estoque_atual),
                )

        elif data.tipo == "PARCIAL":
            # Inventário parcial: filtros específicos
            if data.produto_ids:
                # Por produtos específicos
                for produto_id in data.produto_ids:
                    produto = await self.produto_repository.get_by_id(produto_id)
                    if produto:
                        await self.repository.create_item(
                            ficha_id=ficha_id,
                            produto_id=produto.id,
                            quantidade_sistema=float(produto.estoque_atual),
                        )

            if data.categoria_ids:
                # Por categorias
                for categoria_id in data.categoria_ids:
                    produtos = await self.produto_repository.get_by_categoria(
                        categoria_id
                    )
                    for produto in produtos:
                        await self.repository.create_item(
                            ficha_id=ficha_id,
                            produto_id=produto.id,
                            quantidade_sistema=float(produto.estoque_atual),
                        )

            if data.localizacao_ids:
                # Por localizações (WMS)
                for localizacao_id in data.localizacao_ids:
                    vinculos = await self.wms_repository.list_produtos_localizacao(
                        localizacao_id
                    )
                    for vinculo in vinculos:
                        await self.repository.create_item(
                            ficha_id=ficha_id,
                            produto_id=vinculo.produto_id,
                            quantidade_sistema=float(vinculo.quantidade),
                            localizacao_id=localizacao_id,
                        )

        elif data.tipo == "ROTATIVO":
            # Inventário rotativo: produtos com maior rotatividade (curva A/B)
            # Simplificação: pega produtos com estoque > 0
            produtos = await self.produto_repository.get_all(0, 10000, apenas_ativos=True)
            for produto in produtos:
                if produto.estoque_atual > 0:
                    await self.repository.create_item(
                        ficha_id=ficha_id,
                        produto_id=produto.id,
                        quantidade_sistema=float(produto.estoque_atual),
                    )

    async def get_ficha(self, ficha_id: int) -> FichaInventarioResponse:
        """Busca ficha de inventário por ID"""
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        return FichaInventarioResponse.model_validate(ficha)

    async def list_fichas(
        self,
        page: int = 1,
        page_size: int = 50,
        status: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> FichaInventarioList:
        """Lista fichas de inventário com paginação"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        fichas = await self.repository.list_fichas(skip, page_size, status, tipo)
        total = await self.repository.count_fichas(status, tipo)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return FichaInventarioList(
            items=[FichaInventarioResponse.model_validate(f) for f in fichas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def iniciar_contagem(
        self, ficha_id: int, data: IniciarContagemRequest
    ) -> FichaInventarioResponse:
        """
        Inicia contagem de inventário

        Regras:
        - Apenas fichas com status ABERTA podem iniciar contagem
        """
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        if ficha.status != StatusInventario.ABERTA:
            raise ValidationException(
                f"Apenas fichas com status ABERTA podem iniciar contagem. Status atual: {ficha.status}"
            )

        # Atualiza status para EM_ANDAMENTO
        ficha = await self.repository.update_ficha_status(
            ficha_id, StatusInventario.EM_ANDAMENTO
        )

        if data.observacoes:
            ficha = await self.repository.update_ficha(
                ficha_id, observacoes=data.observacoes
            )

        return FichaInventarioResponse.model_validate(ficha)

    # ==================== ITENS DE INVENTÁRIO ====================

    async def get_itens_ficha(self, ficha_id: int) -> List[ItemInventarioResponse]:
        """Lista todos os itens de uma ficha"""
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        itens = await self.repository.list_itens_ficha(ficha_id)
        return [ItemInventarioResponse.model_validate(item) for item in itens]

    async def registrar_contagem(
        self, data: RegistrarContagemRequest
    ) -> ItemInventarioResponse:
        """
        Registra contagem de um item

        Regras:
        - Calcula divergência automaticamente
        - Registra data e responsável pela contagem
        """
        item = await self.repository.registrar_contagem(
            item_id=data.item_id,
            quantidade_contada=data.quantidade_contada,
            conferido_por_id=data.conferido_por_id,
            justificativa=data.justificativa,
        )

        if not item:
            raise NotFoundException(f"Item de inventário {data.item_id} não encontrado")

        return ItemInventarioResponse.model_validate(item)

    async def finalizar_inventario(
        self, ficha_id: int, data: FinalizarContagemRequest
    ) -> FichaInventarioResponse:
        """
        Finaliza inventário

        Regras:
        - Apenas fichas EM_ANDAMENTO podem ser finalizadas
        - Se ajustar_estoque=True, atualiza estoque dos produtos com divergência
        """
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        if ficha.status != StatusInventario.EM_ANDAMENTO:
            raise ValidationException(
                f"Apenas fichas EM_ANDAMENTO podem ser finalizadas. Status atual: {ficha.status}"
            )

        # Verifica se todos os itens foram contados
        status_contagem = await self.repository.contar_itens_por_status(ficha_id)
        if status_contagem["pendentes"] > 0:
            raise ValidationException(
                f"Ainda há {status_contagem['pendentes']} itens sem contagem"
            )

        # Ajusta estoque se solicitado
        if data.ajustar_estoque:
            await self._ajustar_estoque_por_inventario(ficha_id)

        # Atualiza status para CONCLUIDA
        ficha = await self.repository.update_ficha_status(
            ficha_id, StatusInventario.CONCLUIDA
        )

        if data.observacoes:
            ficha = await self.repository.update_ficha(
                ficha_id, observacoes=data.observacoes
            )

        return FichaInventarioResponse.model_validate(ficha)

    async def _ajustar_estoque_por_inventario(self, ficha_id: int):
        """Ajusta estoque dos produtos baseado na contagem do inventário"""
        itens_com_divergencia = await self.repository.get_itens_com_divergencia(
            ficha_id
        )

        for item in itens_com_divergencia:
            # Atualiza estoque do produto para a quantidade contada
            produto = await self.produto_repository.get_by_id(item.produto_id)
            if produto:
                await self.produto_repository.update(
                    item.produto_id, {"estoque_atual": item.quantidade_contada}
                )

    async def cancelar_inventario(self, ficha_id: int) -> FichaInventarioResponse:
        """Cancela inventário (apenas se não estiver concluído)"""
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        if ficha.status == StatusInventario.CONCLUIDA:
            raise ValidationException("Não é possível cancelar inventário concluído")

        ficha = await self.repository.update_ficha_status(
            ficha_id, StatusInventario.CANCELADA
        )
        return FichaInventarioResponse.model_validate(ficha)

    # ==================== ANÁLISES ====================

    async def calcular_acuracidade(self, ficha_id: int) -> AcuracidadeResponse:
        """
        Calcula acuracidade do inventário

        Acuracidade = (itens sem divergência / total de itens) * 100
        """
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        itens = await self.repository.list_itens_ficha(ficha_id)
        total_itens = len(itens)

        if total_itens == 0:
            return AcuracidadeResponse(
                total_itens=0,
                itens_sem_divergencia=0,
                itens_com_divergencia=0,
                percentual_acuracidade=0,
                divergencia_total_positiva=0,
                divergencia_total_negativa=0,
            )

        itens_sem_divergencia = sum(
            1 for item in itens if item.divergencia == 0 or item.divergencia is None
        )
        itens_com_divergencia = total_itens - itens_sem_divergencia

        percentual_acuracidade = (itens_sem_divergencia / total_itens) * 100

        divergencia_total_positiva = sum(
            float(item.divergencia)
            for item in itens
            if item.divergencia and item.divergencia > 0
        )

        divergencia_total_negativa = sum(
            float(item.divergencia)
            for item in itens
            if item.divergencia and item.divergencia < 0
        )

        return AcuracidadeResponse(
            total_itens=total_itens,
            itens_sem_divergencia=itens_sem_divergencia,
            itens_com_divergencia=itens_com_divergencia,
            percentual_acuracidade=round(percentual_acuracidade, 2),
            divergencia_total_positiva=round(divergencia_total_positiva, 2),
            divergencia_total_negativa=round(abs(divergencia_total_negativa), 2),
        )

    async def get_divergencias(self, ficha_id: int) -> List[DivergenciaItem]:
        """Retorna lista de itens com divergência"""
        ficha = await self.repository.get_ficha_by_id(ficha_id)
        if not ficha:
            raise NotFoundException(f"Ficha de inventário {ficha_id} não encontrada")

        itens_com_divergencia = await self.repository.get_itens_com_divergencia(
            ficha_id
        )

        divergencias = []
        for item in itens_com_divergencia:
            percentual_divergencia = 0
            if item.quantidade_sistema > 0:
                percentual_divergencia = (
                    (item.divergencia / item.quantidade_sistema) * 100
                )

            divergencias.append(
                DivergenciaItem(
                    produto_id=item.produto_id,
                    produto_descricao=item.produto.descricao,
                    codigo_barras=item.produto.codigo_barras,
                    quantidade_sistema=float(item.quantidade_sistema),
                    quantidade_contada=float(item.quantidade_contada),
                    divergencia=float(item.divergencia),
                    percentual_divergencia=round(percentual_divergencia, 2),
                    localizacao_codigo=(
                        item.localizacao.codigo if item.localizacao else None
                    ),
                )
            )

        return divergencias
