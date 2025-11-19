"""
Router para endpoints de Clientes
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.clientes.service import ClienteService
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse,
    ClienteList,
)

router = APIRouter()


@router.post(
    "/",
    response_model=ClienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo cliente",
    description="Cria um novo cliente no sistema",
)
async def create_cliente(
    cliente_data: ClienteCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo cliente.

    **Validações:**
    - CPF/CNPJ único
    - CPF/CNPJ válido
    - E-mail válido (se fornecido)
    - UF válida (se fornecida)

    **Exemplo de requisição:**
    ```json
    {
        "nome": "João da Silva",
        "tipo_pessoa": "PF",
        "cpf_cnpj": "12345678901",
        "email": "joao@example.com",
        "telefone": "(11) 1234-5678",
        "celular": "(11) 98765-4321",
        "data_nascimento": "1990-01-15",
        "endereco": "Rua das Flores",
        "numero": "123",
        "complemento": "Apt 45",
        "bairro": "Centro",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01234567",
        "ativo": true
    }
    ```
    """
    service = ClienteService(db)
    return await service.criar_cliente(cliente_data)


@router.get(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Buscar cliente por ID",
    description="Retorna os dados de um cliente específico",
)
async def get_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """Busca um cliente por ID"""
    service = ClienteService(db)
    return await service.buscar_cliente(cliente_id)


@router.get(
    "/",
    response_model=ClienteList,
    summary="Listar clientes",
    description="Lista todos os clientes com paginação e filtros",
)
async def list_clientes(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(False, description="Listar apenas clientes ativos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista clientes com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, lista apenas clientes ativos
    """
    service = ClienteService(db)
    return await service.listar_clientes(page, page_size, apenas_ativos)


@router.put(
    "/{cliente_id}",
    response_model=ClienteResponse,
    summary="Atualizar cliente",
    description="Atualiza os dados de um cliente",
)
async def update_cliente(
    cliente_id: int,
    cliente_data: ClienteUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza um cliente existente.

    **Validações:**
    - Se alterar CPF/CNPJ, deve ser único
    - CPF/CNPJ deve ser válido
    - E-mail válido (se fornecido)

    **Exemplo de requisição:**
    ```json
    {
        "nome": "João da Silva Santos",
        "email": "joao.santos@example.com",
        "celular": "(11) 99999-8888"
    }
    ```
    """
    service = ClienteService(db)
    return await service.atualizar_cliente(cliente_id, cliente_data)


@router.delete(
    "/{cliente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar cliente",
    description="Inativa um cliente (soft delete)",
)
async def delete_cliente(cliente_id: int, db: AsyncSession = Depends(get_db)):
    """
    Inativa um cliente (soft delete).
    O cliente não é removido do banco, apenas marcado como inativo.
    """
    service = ClienteService(db)
    await service.delete_cliente(cliente_id)
    return None


@router.get(
    "/buscar/search",
    response_model=ClienteList,
    summary="Buscar clientes",
    description="Busca clientes por nome ou CPF/CNPJ",
)
async def search_clientes(
    termo: str = Query(..., min_length=1, description="Termo de busca"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(True, description="Buscar apenas clientes ativos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca clientes por nome ou CPF/CNPJ.

    **Parâmetros:**
    - **termo**: Termo de busca (busca no nome e CPF/CNPJ)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, busca apenas clientes ativos (padrão: True)

    **Exemplo:**
    - `/buscar/search?termo=João` - busca clientes com "João" no nome
    - `/buscar/search?termo=12345678901` - busca cliente com CPF "12345678901"
    """
    service = ClienteService(db)
    return await service.search_clientes(termo, page, page_size, apenas_ativos)


@router.get(
    "/aniversariantes/{mes}",
    response_model=ClienteList,
    summary="Aniversariantes do mês",
    description="Retorna clientes que fazem aniversário no mês especificado",
)
async def get_aniversariantes_mes(
    mes: int,
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna clientes que fazem aniversário em um mês específico.

    **Parâmetros:**
    - **mes**: Mês (1-12)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)

    **Útil para:**
    - Campanhas de marketing de aniversário
    - Envio de mensagens personalizadas
    - Promoções especiais

    **Exemplo:**
    - `/aniversariantes/1` - clientes que fazem aniversário em janeiro
    - `/aniversariantes/12` - clientes que fazem aniversário em dezembro
    """
    service = ClienteService(db)
    return await service.get_aniversariantes_mes(mes, page, page_size)
