"""
Router para Programa de Fidelidade
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.fidelidade.service import FidelidadeService
from app.modules.fidelidade.schemas import (
    ProgramaFidelidadeCreate,
    ProgramaFidelidadeUpdate,
    ProgramaFidelidadeResponse,
    ConsultarSaldoResponse,
    AcumularPontosRequest,
    MovimentacaoPontosResponse,
    ResgatarPontosRequest,
    ResgatarPontosResponse,
    ExtratoResponse,
)

router = APIRouter(prefix="/fidelidade", tags=["Fidelidade"])


# ==================== PROGRAMA ====================


@router.post(
    "/programas",
    response_model=ProgramaFidelidadeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar programa de fidelidade",
    description="Cria programa de fidelidade com regras de acúmulo e resgate",
)
async def criar_programa(
    data: ProgramaFidelidadeCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Cria programa de fidelidade.

    **Configurações:**
    - pontos_por_real: Quantos pontos o cliente ganha por R$ 1,00 gasto
    - valor_ponto_resgate: Valor em R$ de cada ponto no resgate
    - pontos_minimo_resgate: Mínimo de pontos para resgate
    - dias_validade_pontos: Dias de validade (NULL = sem expiração)
    """
    service = FidelidadeService(db)
    return await service.criar_programa(data)


@router.get(
    "/programas/{programa_id}",
    response_model=ProgramaFidelidadeResponse,
    summary="Buscar programa",
    description="Busca programa de fidelidade por ID",
)
async def get_programa(programa_id: int, db: AsyncSession = Depends(get_db)):
    """Busca programa de fidelidade"""
    service = FidelidadeService(db)
    return await service.get_programa(programa_id)


# ==================== PONTOS ====================


@router.get(
    "/clientes/{cliente_id}/saldo",
    response_model=ConsultarSaldoResponse,
    summary="Consultar saldo de pontos",
    description="Consulta saldo de pontos do cliente",
)
async def consultar_saldo(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """
    Consulta saldo de pontos do cliente.

    **Retorna:**
    - Pontos disponíveis
    - Valor disponível para resgate em R$
    - Total acumulado e resgatado historicamente
    """
    service = FidelidadeService(db)
    return await service.consultar_saldo(cliente_id)


@router.post(
    "/acumular",
    response_model=MovimentacaoPontosResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Acumular pontos",
    description="Acumula pontos para cliente baseado em valor de compra",
)
async def acumular_pontos(
    data: AcumularPontosRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Acumula pontos para cliente.

    **Exemplo:**
    ```json
    {
        "cliente_id": 1,
        "valor_compra": 100.00,
        "venda_id": 123,
        "descricao": "Compra de materiais"
    }
    ```

    **Cálculo:**
    - Pontos = valor_compra * programa.pontos_por_real
    """
    service = FidelidadeService(db)
    return await service.acumular_pontos(data)


@router.post(
    "/resgatar",
    response_model=ResgatarPontosResponse,
    summary="Resgatar pontos",
    description="Resgata pontos do cliente para desconto",
)
async def resgatar_pontos(
    data: ResgatarPontosRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Resgata pontos do cliente.

    **Exemplo:**
    ```json
    {
        "cliente_id": 1,
        "pontos": 500,
        "venda_id": 124,
        "descricao": "Desconto em compra"
    }
    ```

    **Retorna:**
    - Valor do desconto em R$
    - Novo saldo de pontos
    """
    service = FidelidadeService(db)
    return await service.resgatar_pontos(data)


@router.get(
    "/clientes/{cliente_id}/extrato",
    response_model=ExtratoResponse,
    summary="Extrato de pontos",
    description="Histórico de movimentações de pontos do cliente",
)
async def extrato_pontos(
    cliente_id: int,
    limit: int = Query(50, ge=1, le=100, description="Limite de registros"),
    db: AsyncSession = Depends(get_db),
):
    """
    Extrato de movimentações de pontos.

    **Retorna:**
    - Saldo atual
    - Histórico de acúmulos e resgates
    - Total de movimentações
    """
    service = FidelidadeService(db)
    return await service.extrato_pontos(cliente_id, limit)
