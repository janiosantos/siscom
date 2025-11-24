"""
Repository Layer para Ordens de Serviço
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.os.models import (
    TipoServico,
    Tecnico,
    OrdemServico,
    ItemOS,
    ApontamentoHoras,
    StatusOS,
)
from app.modules.os.schemas import (
    TipoServicoCreate,
    TipoServicoUpdate,
    TecnicoCreate,
    TecnicoUpdate,
    OrdemServicoCreate,
    OrdemServicoUpdate,
    ItemOSCreate,
    ApontamentoHorasCreate,
)


# ====================================
# TIPO SERVIÇO REPOSITORY
# ====================================


class TipoServicoRepository:
    """Repository para Tipo de Serviço"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tipo_data: TipoServicoCreate) -> TipoServico:
        """Cria novo tipo de serviço"""
        tipo = TipoServico(**tipo_data.model_dump())
        self.session.add(tipo)
        await self.session.flush()
        await self.session.refresh(tipo)
        return tipo

    async def get_by_id(self, tipo_id: int) -> Optional[TipoServico]:
        """Busca tipo de serviço por ID"""
        result = await self.session.execute(
            select(TipoServico).where(TipoServico.id == tipo_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, ativo: Optional[bool] = None
    ) -> List[TipoServico]:
        """Lista todos os tipos de serviço com paginação"""
        query = select(TipoServico)

        if ativo is not None:
            query = query.where(TipoServico.ativo == ativo)

        query = query.offset(skip).limit(limit).order_by(TipoServico.nome)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, ativo: Optional[bool] = None) -> int:
        """Conta total de tipos de serviço"""
        query = select(func.count(TipoServico.id))

        if ativo is not None:
            query = query.where(TipoServico.ativo == ativo)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, tipo_id: int, tipo_data: TipoServicoUpdate
    ) -> Optional[TipoServico]:
        """Atualiza tipo de serviço"""
        tipo = await self.get_by_id(tipo_id)
        if not tipo:
            return None

        update_data = tipo_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tipo, field, value)

        await self.session.flush()
        await self.session.refresh(tipo)
        return tipo

    async def delete(self, tipo_id: int) -> bool:
        """Remove tipo de serviço (soft delete)"""
        tipo = await self.get_by_id(tipo_id)
        if not tipo:
            return False

        tipo.ativo = False
        await self.session.flush()
        return True


# ====================================
# TÉCNICO REPOSITORY
# ====================================


class TecnicoRepository:
    """Repository para Técnico"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tecnico_data: TecnicoCreate) -> Tecnico:
        """Cria novo técnico"""
        tecnico = Tecnico(**tecnico_data.model_dump())
        self.session.add(tecnico)
        await self.session.flush()
        await self.session.refresh(tecnico)
        return tecnico

    async def get_by_id(self, tecnico_id: int) -> Optional[Tecnico]:
        """Busca técnico por ID"""
        result = await self.session.execute(
            select(Tecnico).where(Tecnico.id == tecnico_id)
        )
        return result.scalar_one_or_none()

    async def get_by_cpf(self, cpf: str) -> Optional[Tecnico]:
        """Busca técnico por CPF"""
        result = await self.session.execute(select(Tecnico).where(Tecnico.cpf == cpf))
        return result.scalar_one_or_none()

    async def get_all(
        self, skip: int = 0, limit: int = 100, ativo: Optional[bool] = None
    ) -> List[Tecnico]:
        """Lista todos os técnicos com paginação"""
        query = select(Tecnico)

        if ativo is not None:
            query = query.where(Tecnico.ativo == ativo)

        query = query.offset(skip).limit(limit).order_by(Tecnico.nome)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_disponiveis(self, skip: int = 0, limit: int = 100) -> List[Tecnico]:
        """Lista técnicos disponíveis (ativos)"""
        return await self.get_all(skip=skip, limit=limit, ativo=True)

    async def get_por_especialidade(
        self, especialidade: str, skip: int = 0, limit: int = 100
    ) -> List[Tecnico]:
        """Busca técnicos por especialidade"""
        query = (
            select(Tecnico)
            .where(
                and_(
                    Tecnico.ativo == True,
                    Tecnico.especialidades.ilike(f"%{especialidade}%"),
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(Tecnico.nome)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(self, ativo: Optional[bool] = None) -> int:
        """Conta total de técnicos"""
        query = select(func.count(Tecnico.id))

        if ativo is not None:
            query = query.where(Tecnico.ativo == ativo)

        result = await self.session.execute(query)
        return result.scalar_one()

    async def update(
        self, tecnico_id: int, tecnico_data: TecnicoUpdate
    ) -> Optional[Tecnico]:
        """Atualiza técnico"""
        tecnico = await self.get_by_id(tecnico_id)
        if not tecnico:
            return None

        update_data = tecnico_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tecnico, field, value)

        await self.session.flush()
        await self.session.refresh(tecnico)
        return tecnico

    async def delete(self, tecnico_id: int) -> bool:
        """Remove técnico (soft delete)"""
        tecnico = await self.get_by_id(tecnico_id)
        if not tecnico:
            return False

        tecnico.ativo = False
        await self.session.flush()
        return True


# ====================================
# ORDEM SERVIÇO REPOSITORY
# ====================================


class OrdemServicoRepository:
    """Repository para Ordem de Serviço"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_os(self, os_data: OrdemServicoCreate) -> OrdemServico:
        """Cria nova ordem de serviço"""
        os = OrdemServico(**os_data.model_dump())
        self.session.add(os)
        await self.session.flush()
        await self.session.refresh(os)
        return os

    async def create_item_os(self, os_id: int, item_data: ItemOSCreate) -> ItemOS:
        """Adiciona item (material) à OS"""
        total_item = item_data.quantidade * item_data.preco_unitario

        item = ItemOS(
            os_id=os_id,
            produto_id=item_data.produto_id,
            quantidade=item_data.quantidade,
            preco_unitario=item_data.preco_unitario,
            total_item=total_item,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def create_apontamento(
        self, os_id: int, apontamento_data: ApontamentoHorasCreate
    ) -> ApontamentoHoras:
        """Adiciona apontamento de horas à OS"""
        apontamento = ApontamentoHoras(
            os_id=os_id,
            tecnico_id=apontamento_data.tecnico_id,
            data=apontamento_data.data,
            horas_trabalhadas=apontamento_data.horas_trabalhadas,
            descricao=apontamento_data.descricao,
        )
        self.session.add(apontamento)
        await self.session.flush()
        await self.session.refresh(apontamento)
        return apontamento

    async def get_by_id(self, os_id: int) -> Optional[OrdemServico]:
        """Busca OS completa por ID"""
        result = await self.session.execute(
            select(OrdemServico).where(OrdemServico.id == os_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        cliente_id: Optional[int] = None,
        tecnico_id: Optional[int] = None,
        status: Optional[StatusOS] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> List[OrdemServico]:
        """Lista ordens de serviço com filtros"""
        query = select(OrdemServico)

        filters = []
        if cliente_id:
            filters.append(OrdemServico.cliente_id == cliente_id)
        if tecnico_id:
            filters.append(OrdemServico.tecnico_id == tecnico_id)
        if status:
            filters.append(OrdemServico.status == status)
        if data_inicio:
            filters.append(OrdemServico.data_abertura >= data_inicio)
        if data_fim:
            filters.append(OrdemServico.data_abertura <= data_fim)

        if filters:
            query = query.where(and_(*filters))

        query = query.offset(skip).limit(limit).order_by(OrdemServico.data_abertura.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        cliente_id: Optional[int] = None,
        tecnico_id: Optional[int] = None,
        status: Optional[StatusOS] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> int:
        """Conta ordens de serviço com filtros"""
        query = select(func.count(OrdemServico.id))

        filters = []
        if cliente_id:
            filters.append(OrdemServico.cliente_id == cliente_id)
        if tecnico_id:
            filters.append(OrdemServico.tecnico_id == tecnico_id)
        if status:
            filters.append(OrdemServico.status == status)
        if data_inicio:
            filters.append(OrdemServico.data_abertura >= data_inicio)
        if data_fim:
            filters.append(OrdemServico.data_abertura <= data_fim)

        if filters:
            query = query.where(and_(*filters))

        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_por_cliente(
        self, cliente_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrdemServico]:
        """Busca OSs de um cliente"""
        return await self.get_all(
            skip=skip, limit=limit, cliente_id=cliente_id
        )

    async def get_por_tecnico(
        self, tecnico_id: int, skip: int = 0, limit: int = 100
    ) -> List[OrdemServico]:
        """Busca OSs de um técnico"""
        return await self.get_all(
            skip=skip, limit=limit, tecnico_id=tecnico_id
        )

    async def get_por_status(
        self, status: StatusOS, skip: int = 0, limit: int = 100
    ) -> List[OrdemServico]:
        """Busca OSs por status"""
        return await self.get_all(skip=skip, limit=limit, status=status)

    async def get_os_abertas(self, skip: int = 0, limit: int = 100) -> List[OrdemServico]:
        """Busca OSs abertas"""
        return await self.get_por_status(StatusOS.ABERTA, skip=skip, limit=limit)

    async def get_os_atrasadas(
        self, skip: int = 0, limit: int = 100
    ) -> List[OrdemServico]:
        """Busca OSs atrasadas (data_prevista < hoje e status != CONCLUIDA/CANCELADA/FATURADA)"""
        hoje = datetime.now()

        query = (
            select(OrdemServico)
            .where(
                and_(
                    OrdemServico.data_prevista < hoje,
                    OrdemServico.status.notin_(
                        [StatusOS.CONCLUIDA, StatusOS.CANCELADA, StatusOS.FATURADA]
                    ),
                )
            )
            .offset(skip)
            .limit(limit)
            .order_by(OrdemServico.data_prevista)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update(
        self, os_id: int, os_data: OrdemServicoUpdate
    ) -> Optional[OrdemServico]:
        """Atualiza ordem de serviço"""
        os = await self.get_by_id(os_id)
        if not os:
            return None

        update_data = os_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(os, field, value)

        await self.session.flush()
        await self.session.refresh(os)
        return os

    async def atualizar_status(self, os_id: int, status: StatusOS) -> Optional[OrdemServico]:
        """Atualiza status da OS"""
        os = await self.get_by_id(os_id)
        if not os:
            return None

        os.status = status
        await self.session.flush()
        await self.session.refresh(os)
        return os

    async def calcular_valor_total(self, os_id: int) -> float:
        """
        Calcula valor total da OS
        valor_total = valor_mao_obra + soma(itens.total_item)

        Nota: O cálculo de horas deve ser feito no service layer
        """
        os = await self.get_by_id(os_id)
        if not os:
            return 0.0

        # Soma valor de mão de obra
        valor_total = float(os.valor_mao_obra)

        # Soma itens (materiais)
        query = select(func.sum(ItemOS.total_item)).where(ItemOS.os_id == os_id)
        result = await self.session.execute(query)
        soma_itens = result.scalar_one_or_none() or 0.0

        valor_total += float(soma_itens)

        return round(valor_total, 2)

    async def atualizar_valor_total(self, os_id: int, valor_total: float) -> None:
        """Atualiza valor total da OS"""
        os = await self.get_by_id(os_id)
        if os:
            os.valor_total = valor_total
            await self.session.flush()
