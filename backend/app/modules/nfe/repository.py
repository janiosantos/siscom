"""
Repository para Notas Fiscais
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.nfe.models import NotaFiscal, TipoNota, StatusNota
from app.modules.nfe.schemas import NotaFiscalCreate


class NotaFiscalRepository:
    """Repository para operações de banco de dados de Notas Fiscais"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, nota_data: NotaFiscalCreate) -> NotaFiscal:
        """
        Cria uma nova nota fiscal

        Args:
            nota_data: Dados da nota fiscal

        Returns:
            NotaFiscal criada
        """
        nota = NotaFiscal(
            tipo=nota_data.tipo,
            numero=nota_data.numero,
            serie=nota_data.serie,
            chave_acesso=nota_data.chave_acesso,
            data_emissao=nota_data.data_emissao,
            fornecedor_id=nota_data.fornecedor_id,
            cliente_id=nota_data.cliente_id,
            venda_id=nota_data.venda_id,
            valor_produtos=nota_data.valor_produtos,
            valor_total=nota_data.valor_total,
            valor_icms=nota_data.valor_icms,
            valor_ipi=nota_data.valor_ipi,
            status=nota_data.status,
            xml_nfe=nota_data.xml_nfe,
            observacoes=nota_data.observacoes,
        )

        self.session.add(nota)
        await self.session.flush()
        await self.session.refresh(nota)

        return nota

    async def get_by_id(self, nota_id: int) -> Optional[NotaFiscal]:
        """
        Busca nota fiscal por ID

        Args:
            nota_id: ID da nota

        Returns:
            NotaFiscal ou None se não encontrada
        """
        result = await self.session.execute(
            select(NotaFiscal).where(NotaFiscal.id == nota_id)
        )
        return result.scalar_one_or_none()

    async def get_by_chave(self, chave_acesso: str) -> Optional[NotaFiscal]:
        """
        Busca nota fiscal por chave de acesso

        Args:
            chave_acesso: Chave de acesso da nota

        Returns:
            NotaFiscal ou None se não encontrada
        """
        result = await self.session.execute(
            select(NotaFiscal).where(NotaFiscal.chave_acesso == chave_acesso)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        tipo: Optional[TipoNota] = None,
        status: Optional[StatusNota] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        fornecedor_id: Optional[int] = None,
        venda_id: Optional[int] = None,
    ) -> List[NotaFiscal]:
        """
        Lista notas fiscais com paginação e filtros

        Args:
            skip: Quantos registros pular
            limit: Limite de registros
            tipo: Filtrar por tipo de nota
            status: Filtrar por status
            data_inicio: Data inicial do período
            data_fim: Data final do período
            fornecedor_id: Filtrar por fornecedor
            venda_id: Filtrar por venda

        Returns:
            Lista de NotaFiscal
        """
        query = select(NotaFiscal)

        if tipo:
            query = query.where(NotaFiscal.tipo == tipo)

        if status:
            query = query.where(NotaFiscal.status == status)

        if data_inicio:
            query = query.where(NotaFiscal.data_emissao >= data_inicio)

        if data_fim:
            query = query.where(NotaFiscal.data_emissao <= data_fim)

        if fornecedor_id:
            query = query.where(NotaFiscal.fornecedor_id == fornecedor_id)

        if venda_id:
            query = query.where(NotaFiscal.venda_id == venda_id)

        query = query.order_by(NotaFiscal.data_emissao.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        tipo: Optional[TipoNota] = None,
        status: Optional[StatusNota] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        fornecedor_id: Optional[int] = None,
        venda_id: Optional[int] = None,
    ) -> int:
        """
        Conta total de notas fiscais com filtros

        Args:
            tipo: Filtrar por tipo de nota
            status: Filtrar por status
            data_inicio: Data inicial do período
            data_fim: Data final do período
            fornecedor_id: Filtrar por fornecedor
            venda_id: Filtrar por venda

        Returns:
            Total de registros
        """
        query = select(func.count(NotaFiscal.id))

        if tipo:
            query = query.where(NotaFiscal.tipo == tipo)

        if status:
            query = query.where(NotaFiscal.status == status)

        if data_inicio:
            query = query.where(NotaFiscal.data_emissao >= data_inicio)

        if data_fim:
            query = query.where(NotaFiscal.data_emissao <= data_fim)

        if fornecedor_id:
            query = query.where(NotaFiscal.fornecedor_id == fornecedor_id)

        if venda_id:
            query = query.where(NotaFiscal.venda_id == venda_id)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_por_venda(self, venda_id: int) -> List[NotaFiscal]:
        """
        Busca notas fiscais por venda

        Args:
            venda_id: ID da venda

        Returns:
            Lista de NotaFiscal
        """
        result = await self.session.execute(
            select(NotaFiscal)
            .where(NotaFiscal.venda_id == venda_id)
            .order_by(NotaFiscal.data_emissao.desc())
        )
        return list(result.scalars().all())

    async def get_por_tipo(
        self, tipo: TipoNota, skip: int = 0, limit: int = 50
    ) -> List[NotaFiscal]:
        """
        Busca notas fiscais por tipo

        Args:
            tipo: Tipo da nota
            skip: Quantos registros pular
            limit: Limite de registros

        Returns:
            Lista de NotaFiscal
        """
        result = await self.session.execute(
            select(NotaFiscal)
            .where(NotaFiscal.tipo == tipo)
            .order_by(NotaFiscal.data_emissao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def atualizar_status(
        self, nota_id: int, status: StatusNota, observacao: Optional[str] = None
    ) -> Optional[NotaFiscal]:
        """
        Atualiza o status de uma nota fiscal

        Args:
            nota_id: ID da nota
            status: Novo status
            observacao: Observação adicional

        Returns:
            NotaFiscal atualizada ou None se não encontrada
        """
        nota = await self.get_by_id(nota_id)
        if not nota:
            return None

        nota.status = status
        if observacao:
            nota.observacoes = (
                f"{nota.observacoes}\n{observacao}" if nota.observacoes else observacao
            )

        await self.session.flush()
        await self.session.refresh(nota)

        return nota

    async def registrar_autorizacao(
        self, nota_id: int, protocolo: str, data_autorizacao: datetime
    ) -> Optional[NotaFiscal]:
        """
        Registra a autorização de uma nota fiscal

        Args:
            nota_id: ID da nota
            protocolo: Protocolo de autorização
            data_autorizacao: Data da autorização

        Returns:
            NotaFiscal atualizada ou None se não encontrada
        """
        nota = await self.get_by_id(nota_id)
        if not nota:
            return None

        nota.status = StatusNota.AUTORIZADA
        nota.protocolo_autorizacao = protocolo
        nota.data_autorizacao = data_autorizacao

        await self.session.flush()
        await self.session.refresh(nota)

        return nota

    async def get_notas_periodo(
        self, data_inicio: datetime, data_fim: datetime, skip: int = 0, limit: int = 50
    ) -> List[NotaFiscal]:
        """
        Busca notas fiscais por período

        Args:
            data_inicio: Data inicial
            data_fim: Data final
            skip: Quantos registros pular
            limit: Limite de registros

        Returns:
            Lista de NotaFiscal
        """
        result = await self.session.execute(
            select(NotaFiscal)
            .where(NotaFiscal.data_emissao >= data_inicio)
            .where(NotaFiscal.data_emissao <= data_fim)
            .order_by(NotaFiscal.data_emissao.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())
