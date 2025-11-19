"""
Rotas da API para Ordens de Serviço
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.os.service import OSService
from app.modules.os.schemas import (
    TipoServicoCreate,
    TipoServicoUpdate,
    TipoServicoResponse,
    TipoServicoList,
    TecnicoCreate,
    TecnicoUpdate,
    TecnicoResponse,
    TecnicoList,
    OrdemServicoCreate,
    OrdemServicoUpdate,
    OrdemServicoResponse,
    OrdemServicoList,
    ItemOSResponse,
    ApontamentoHorasResponse,
    StatusOSEnum,
    AtribuirTecnicoRequest,
    IniciarOSRequest,
    AdicionarMaterialRequest,
    ApontarHorasRequest,
    FinalizarOSRequest,
    FaturarOSRequest,
    CancelarOSRequest,
)

router = APIRouter(prefix="/os", tags=["Ordens de Serviço"])


# ====================================
# TIPOS DE SERVIÇO
# ====================================


@router.post(
    "/tipos-servico",
    response_model=TipoServicoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Tipo de Serviço",
)
async def criar_tipo_servico(
    tipo_data: TipoServicoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo tipo de serviço"""
    service = OSService(db)
    return await service.criar_tipo_servico(tipo_data)


@router.get(
    "/tipos-servico",
    response_model=TipoServicoList,
    summary="Listar Tipos de Serviço",
)
async def listar_tipos_servico(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: AsyncSession = Depends(get_db),
):
    """Lista tipos de serviço com paginação e filtros"""
    service = OSService(db)
    return await service.list_tipos_servico(page=page, page_size=page_size, ativo=ativo)


@router.get(
    "/tipos-servico/{tipo_id}",
    response_model=TipoServicoResponse,
    summary="Buscar Tipo de Serviço",
)
async def buscar_tipo_servico(
    tipo_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca tipo de serviço por ID"""
    service = OSService(db)
    return await service.get_tipo_servico(tipo_id)


@router.put(
    "/tipos-servico/{tipo_id}",
    response_model=TipoServicoResponse,
    summary="Atualizar Tipo de Serviço",
)
async def atualizar_tipo_servico(
    tipo_id: int,
    tipo_data: TipoServicoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza tipo de serviço"""
    service = OSService(db)
    return await service.atualizar_tipo_servico(tipo_id, tipo_data)


# ====================================
# TÉCNICOS
# ====================================


@router.post(
    "/tecnicos",
    response_model=TecnicoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Técnico",
)
async def criar_tecnico(
    tecnico_data: TecnicoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo técnico"""
    service = OSService(db)
    return await service.criar_tecnico(tecnico_data)


@router.get(
    "/tecnicos",
    response_model=TecnicoList,
    summary="Listar Técnicos",
)
async def listar_tecnicos(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    ativo: Optional[bool] = Query(None, description="Filtrar por status ativo"),
    db: AsyncSession = Depends(get_db),
):
    """Lista técnicos com paginação e filtros"""
    service = OSService(db)
    return await service.list_tecnicos(page=page, page_size=page_size, ativo=ativo)


@router.get(
    "/tecnicos/{tecnico_id}",
    response_model=TecnicoResponse,
    summary="Buscar Técnico",
)
async def buscar_tecnico(
    tecnico_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca técnico por ID"""
    service = OSService(db)
    return await service.get_tecnico(tecnico_id)


@router.put(
    "/tecnicos/{tecnico_id}",
    response_model=TecnicoResponse,
    summary="Atualizar Técnico",
)
async def atualizar_tecnico(
    tecnico_id: int,
    tecnico_data: TecnicoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza técnico"""
    service = OSService(db)
    return await service.atualizar_tecnico(tecnico_id, tecnico_data)


# ====================================
# ORDENS DE SERVIÇO
# ====================================


@router.post(
    "/",
    response_model=OrdemServicoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir Ordem de Serviço",
)
async def abrir_os(
    os_data: OrdemServicoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Abre uma nova ordem de serviço

    Valida cliente, técnico, tipo de serviço e produto (se equipamento).
    Registra número de série se informado.
    """
    service = OSService(db)
    return await service.abrir_os(os_data)


@router.get(
    "/",
    response_model=OrdemServicoList,
    summary="Listar Ordens de Serviço",
)
async def listar_os(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    cliente_id: Optional[int] = Query(None, description="Filtrar por cliente"),
    tecnico_id: Optional[int] = Query(None, description="Filtrar por técnico"),
    status: Optional[StatusOSEnum] = Query(None, description="Filtrar por status"),
    data_inicio: Optional[datetime] = Query(None, description="Data inicial"),
    data_fim: Optional[datetime] = Query(None, description="Data final"),
    db: AsyncSession = Depends(get_db),
):
    """Lista ordens de serviço com paginação e filtros"""
    service = OSService(db)
    return await service.list_os(
        page=page,
        page_size=page_size,
        cliente_id=cliente_id,
        tecnico_id=tecnico_id,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )


@router.get(
    "/abertas",
    response_model=OrdemServicoList,
    summary="Listar OSs Abertas",
)
async def listar_os_abertas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """Lista ordens de serviço com status ABERTA"""
    service = OSService(db)
    return await service.get_os_abertas(page=page, page_size=page_size)


@router.get(
    "/atrasadas",
    response_model=OrdemServicoList,
    summary="Listar OSs Atrasadas",
)
async def listar_os_atrasadas(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """Lista ordens de serviço atrasadas (data_prevista < hoje e não concluída)"""
    service = OSService(db)
    return await service.get_os_atrasadas(page=page, page_size=page_size)


@router.get(
    "/tecnico/{tecnico_id}/agenda",
    response_model=OrdemServicoList,
    summary="Agenda do Técnico",
)
async def agenda_tecnico(
    tecnico_id: int,
    data_inicio: datetime = Query(..., description="Data inicial do período"),
    data_fim: datetime = Query(..., description="Data final do período"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """Busca agenda de um técnico por período"""
    service = OSService(db)
    return await service.get_agenda_tecnico(
        tecnico_id=tecnico_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{os_id}",
    response_model=OrdemServicoResponse,
    summary="Buscar Ordem de Serviço",
)
async def buscar_os(
    os_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca ordem de serviço completa por ID"""
    service = OSService(db)
    return await service.get_os(os_id)


@router.put(
    "/{os_id}",
    response_model=OrdemServicoResponse,
    summary="Atualizar Ordem de Serviço",
)
async def atualizar_os(
    os_id: int,
    os_data: OrdemServicoUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza ordem de serviço (não permite atualizar OS concluída/cancelada/faturada)"""
    service = OSService(db)
    return await service.atualizar_os(os_id, os_data)


@router.post(
    "/{os_id}/atribuir-tecnico",
    response_model=OrdemServicoResponse,
    summary="Atribuir Técnico",
)
async def atribuir_tecnico(
    os_id: int,
    request: AtribuirTecnicoRequest,
    db: AsyncSession = Depends(get_db),
):
    """Atribui ou reatribui técnico a uma OS"""
    service = OSService(db)
    return await service.atribuir_tecnico(os_id, request.tecnico_id)


@router.post(
    "/{os_id}/iniciar",
    response_model=OrdemServicoResponse,
    summary="Iniciar Ordem de Serviço",
)
async def iniciar_os(
    os_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Inicia uma OS (muda status para EM_ANDAMENTO)"""
    service = OSService(db)
    return await service.iniciar_os(os_id)


@router.post(
    "/{os_id}/adicionar-material",
    response_model=ItemOSResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar Material à OS",
)
async def adicionar_material(
    os_id: int,
    material_data: AdicionarMaterialRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Adiciona material (item) à OS e dá baixa automática no estoque

    O estoque do produto é decrementado automaticamente.
    """
    service = OSService(db)
    from app.modules.os.schemas import ItemOSCreate

    item_data = ItemOSCreate(
        produto_id=material_data.produto_id,
        quantidade=material_data.quantidade,
        preco_unitario=material_data.preco_unitario,
    )
    return await service.adicionar_material_os(os_id, item_data)


@router.post(
    "/{os_id}/apontar-horas",
    response_model=ApontamentoHorasResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apontar Horas Trabalhadas",
)
async def apontar_horas(
    os_id: int,
    apontamento_data: ApontarHorasRequest,
    db: AsyncSession = Depends(get_db),
):
    """Registra apontamento de horas trabalhadas na OS"""
    service = OSService(db)
    from app.modules.os.schemas import ApontamentoHorasCreate

    apontamento = ApontamentoHorasCreate(
        tecnico_id=apontamento_data.tecnico_id,
        data=apontamento_data.data,
        horas_trabalhadas=apontamento_data.horas_trabalhadas,
        descricao=apontamento_data.descricao,
    )
    return await service.apontar_horas(os_id, apontamento)


@router.post(
    "/{os_id}/finalizar",
    response_model=OrdemServicoResponse,
    summary="Finalizar Ordem de Serviço",
)
async def finalizar_os(
    os_id: int,
    finalizar_data: FinalizarOSRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Finaliza OS (muda status para CONCLUIDA)

    Preenche data_conclusao, descricao_solucao e calcula valor_total final.
    """
    service = OSService(db)
    return await service.finalizar_os(os_id, finalizar_data)


@router.post(
    "/{os_id}/faturar",
    response_model=OrdemServicoResponse,
    summary="Faturar Ordem de Serviço",
)
async def faturar_os(
    os_id: int,
    faturar_data: FaturarOSRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Fatura OS (muda status para FATURADA)

    Cria conta a receber no financeiro e muda status para FATURADA.
    Somente OSs CONCLUIDAS podem ser faturadas.
    """
    service = OSService(db)
    return await service.faturar_os(os_id, faturar_data)


@router.delete(
    "/{os_id}",
    response_model=OrdemServicoResponse,
    summary="Cancelar Ordem de Serviço",
)
async def cancelar_os(
    os_id: int,
    cancelar_data: CancelarOSRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancela ordem de serviço

    Não permite cancelar OSs FATURADAS.
    Registra motivo do cancelamento nas observações.
    """
    service = OSService(db)
    return await service.cancelar_os(os_id, cancelar_data.motivo)
