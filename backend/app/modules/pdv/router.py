"""
Router para endpoints de PDV
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.pdv.service import PDVService
from app.modules.pdv.schemas import (
    AbrirCaixaCreate,
    FecharCaixaCreate,
    CaixaResponse,
    MovimentacaoCaixaResponse,
    MovimentacoesCaixaList,
    VendaPDVCreate,
    SangriaCreate,
    SuprimentoCreate,
    SaldoCaixaResponse,
)
from app.modules.vendas.schemas import VendaResponse

router = APIRouter()


@router.post(
    "/caixa/abrir",
    response_model=CaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir caixa",
    description="Abre um novo caixa para o operador",
)
async def abrir_caixa(
    caixa_data: AbrirCaixaCreate, db: AsyncSession = Depends(get_db)
):
    """
    Abre um novo caixa para o operador.

    **Regras:**
    - Não pode haver outro caixa aberto para o mesmo operador
    - Valor de abertura não pode ser negativo

    **Exemplo de requisição:**
    ```json
    {
        "operador_id": 1,
        "valor_abertura": 100.00
    }
    ```
    """
    service = PDVService(db)
    return await service.abrir_caixa(caixa_data)


@router.post(
    "/caixa/fechar",
    response_model=CaixaResponse,
    summary="Fechar caixa",
    description="Fecha o caixa aberto do operador",
)
async def fechar_caixa(
    operador_id: int = Query(..., description="ID do operador"),
    fechamento_data: FecharCaixaCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Fecha o caixa aberto do operador.

    **Regras:**
    - Deve existir um caixa aberto para o operador
    - Calcula saldo esperado e compara com valor informado

    **Exemplo de requisição:**
    ```json
    {
        "valor_fechamento": 1250.50
    }
    ```

    **Exemplo de uso:**
    - POST /pdv/caixa/fechar?operador_id=1
    """
    service = PDVService(db)
    return await service.fechar_caixa(operador_id, fechamento_data)


@router.get(
    "/caixa/atual",
    response_model=CaixaResponse,
    summary="Buscar caixa atual",
    description="Retorna o caixa aberto do operador",
)
async def get_caixa_atual(
    operador_id: int = Query(..., description="ID do operador"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna o caixa aberto do operador.

    **Parâmetros:**
    - **operador_id**: ID do operador (obrigatório)

    **Exemplo de uso:**
    - GET /pdv/caixa/atual?operador_id=1
    """
    service = PDVService(db)
    return await service.get_caixa_atual(operador_id)


@router.get(
    "/caixa/{caixa_id}",
    response_model=CaixaResponse,
    summary="Buscar caixa por ID",
    description="Retorna os dados de um caixa específico",
)
async def get_caixa(caixa_id: int, db: AsyncSession = Depends(get_db)):
    """Busca um caixa por ID"""
    service = PDVService(db)
    return await service.get_caixa_by_id(caixa_id)


@router.post(
    "/venda",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venda no PDV",
    description="Registra uma venda rápida no PDV",
)
async def registrar_venda_pdv(
    operador_id: int = Query(..., description="ID do operador"),
    venda_data: VendaPDVCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma venda rápida no PDV.

    **Regras:**
    - Deve existir um caixa aberto para o operador
    - Cria a venda através do VendasService
    - Registra movimentação de entrada no caixa automaticamente
    - Valida estoque e dá baixa automaticamente

    **Exemplo de requisição:**
    ```json
    {
        "cliente_id": 1,
        "forma_pagamento": "DINHEIRO",
        "desconto": 0.0,
        "observacoes": "Venda balcão",
        "itens": [
            {
                "produto_id": 1,
                "quantidade": 2.0,
                "preco_unitario": 32.90,
                "desconto_item": 0.0
            }
        ]
    }
    ```

    **Exemplo de uso:**
    - POST /pdv/venda?operador_id=1
    """
    service = PDVService(db)
    return await service.registrar_venda_pdv(operador_id, venda_data)


@router.post(
    "/sangria",
    response_model=MovimentacaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sangria",
    description="Registra uma sangria (retirada de dinheiro) do caixa",
)
async def registrar_sangria(
    operador_id: int = Query(..., description="ID do operador"),
    sangria_data: SangriaCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma sangria (retirada de dinheiro) do caixa.

    **Regras:**
    - Deve existir um caixa aberto para o operador
    - Descrição é obrigatória
    - Valor deve ser maior que zero

    **Exemplo de requisição:**
    ```json
    {
        "valor": 500.00,
        "descricao": "Sangria para depósito bancário"
    }
    ```

    **Exemplo de uso:**
    - POST /pdv/sangria?operador_id=1
    """
    service = PDVService(db)
    return await service.registrar_sangria(operador_id, sangria_data)


@router.post(
    "/suprimento",
    response_model=MovimentacaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar suprimento",
    description="Registra um suprimento (entrada de dinheiro) no caixa",
)
async def registrar_suprimento(
    operador_id: int = Query(..., description="ID do operador"),
    suprimento_data: SuprimentoCreate = ...,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra um suprimento (entrada de dinheiro) no caixa.

    **Regras:**
    - Deve existir um caixa aberto para o operador
    - Descrição é obrigatória
    - Valor deve ser maior que zero

    **Exemplo de requisição:**
    ```json
    {
        "valor": 200.00,
        "descricao": "Suprimento para troco"
    }
    ```

    **Exemplo de uso:**
    - POST /pdv/suprimento?operador_id=1
    """
    service = PDVService(db)
    return await service.registrar_suprimento(operador_id, suprimento_data)


@router.get(
    "/caixa/{caixa_id}/movimentacoes",
    response_model=MovimentacoesCaixaList,
    summary="Listar movimentações do caixa",
    description="Retorna todas as movimentações de um caixa",
)
async def get_movimentacoes_caixa(
    caixa_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Retorna todas as movimentações de um caixa.

    **Parâmetros:**
    - **caixa_id**: ID do caixa

    **Retorno:**
    Lista com todas as movimentações (ENTRADA, SAIDA, SANGRIA, SUPRIMENTO)

    **Exemplo de uso:**
    - GET /pdv/caixa/1/movimentacoes
    """
    service = PDVService(db)
    return await service.get_movimentacoes_caixa(caixa_id)


@router.get(
    "/caixa/{caixa_id}/saldo",
    response_model=SaldoCaixaResponse,
    summary="Calcular saldo do caixa",
    description="Retorna o saldo atual e esperado do caixa com detalhamento",
)
async def calcular_saldo_caixa(caixa_id: int, db: AsyncSession = Depends(get_db)):
    """
    Calcula e retorna o saldo do caixa com detalhamento.

    **Parâmetros:**
    - **caixa_id**: ID do caixa

    **Retorno:**
    ```json
    {
        "caixa_id": 1,
        "operador_id": 1,
        "data_abertura": "2025-01-20T08:00:00",
        "valor_abertura": 100.00,
        "total_entradas": 1500.00,
        "total_saidas": 0.00,
        "total_sangrias": 500.00,
        "total_suprimentos": 200.00,
        "saldo_atual": 1300.00,
        "saldo_esperado": 1300.00,
        "status": "ABERTO"
    }
    ```

    **Cálculo do saldo esperado:**
    - Saldo Esperado = Valor Abertura + Entradas + Suprimentos - Saídas - Sangrias

    **Exemplo de uso:**
    - GET /pdv/caixa/1/saldo
    """
    service = PDVService(db)
    return await service.calcular_saldo_caixa(caixa_id)


# ========== ROTAS ALTERNATIVAS COM CAIXA_ID NA URL ==========


@router.post(
    "/caixa/{caixa_id}/fechar",
    response_model=CaixaResponse,
    summary="Fechar caixa por ID",
    description="Fecha um caixa específico pelo ID",
)
async def fechar_caixa_por_id(
    caixa_id: int,
    fechamento_data: FecharCaixaCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Fecha um caixa específico pelo ID.
    """
    service = PDVService(db)
    # Buscar o caixa para pegar o operador_id
    caixa = await service.get_caixa_by_id(caixa_id)
    return await service.fechar_caixa(caixa.operador_id, fechamento_data)


@router.post(
    "/caixa/{caixa_id}/movimentacoes",
    response_model=MovimentacaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar movimentação no caixa",
    description="Registra uma movimentação (entrada ou saída) no caixa",
)
async def criar_movimentacao(
    caixa_id: int,
    tipo: str = Query(..., description="Tipo de movimentação: ENTRADA ou SAIDA"),
    valor: float = Query(..., description="Valor da movimentação"),
    descricao: str = Query(None, description="Descrição da movimentação"),
    db: AsyncSession = Depends(get_db),
):
    """
    Cria uma movimentação no caixa.
    """
    from app.modules.pdv.schemas import MovimentacaoCaixaCreate

    movimentacao_data = MovimentacaoCaixaCreate(
        tipo=tipo,
        valor=valor,
        descricao=descricao
    )
    service = PDVService(db)
    return await service.criar_movimentacao(caixa_id, movimentacao_data)


@router.post(
    "/caixa/{caixa_id}/sangria",
    response_model=MovimentacaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sangria por ID do caixa",
    description="Registra uma sangria no caixa específico",
)
async def registrar_sangria_por_id(
    caixa_id: int,
    sangria_data: SangriaCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma sangria no caixa específico.
    """
    service = PDVService(db)
    # Buscar o caixa para pegar o operador_id
    caixa = await service.get_caixa_by_id(caixa_id)
    return await service.registrar_sangria(caixa.operador_id, sangria_data)


@router.post(
    "/caixa/{caixa_id}/suprimento",
    response_model=MovimentacaoCaixaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar suprimento por ID do caixa",
    description="Registra um suprimento no caixa específico",
)
async def registrar_suprimento_por_id(
    caixa_id: int,
    suprimento_data: SuprimentoCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra um suprimento no caixa específico.
    """
    service = PDVService(db)
    # Buscar o caixa para pegar o operador_id
    caixa = await service.get_caixa_by_id(caixa_id)
    return await service.registrar_suprimento(caixa.operador_id, suprimento_data)


@router.post(
    "/caixa/{caixa_id}/vendas",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venda no PDV por ID do caixa",
    description="Registra uma venda rápida no PDV usando o ID do caixa",
)
async def registrar_venda_pdv_por_id(
    caixa_id: int,
    venda_data: VendaPDVCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma venda rápida no PDV usando o ID do caixa.
    """
    service = PDVService(db)
    # Buscar o caixa para pegar o operador_id
    caixa = await service.get_caixa_by_id(caixa_id)
    return await service.registrar_venda_pdv(caixa.operador_id, venda_data)
