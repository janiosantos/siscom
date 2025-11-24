"""
Router para endpoints de Fornecedores
"""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.modules.fornecedores.service import FornecedorService
from app.modules.fornecedores.schemas import (
    FornecedorCreate,
    FornecedorUpdate,
    FornecedorResponse,
    FornecedorList,
)

router = APIRouter()


@router.post(
    "/",
    response_model=FornecedorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo fornecedor",
    description="Cria um novo fornecedor no sistema",
)
async def create_fornecedor(
    fornecedor_data: FornecedorCreate, db: AsyncSession = Depends(get_db)
):
    """
    Cria um novo fornecedor.

    **Validações:**
    - CNPJ único
    - CNPJ válido
    - E-mail válido (se fornecido)
    - UF válida (se fornecida)

    **Exemplo de requisição:**
    ```json
    {
        "razao_social": "Fornecedor ABC Ltda",
        "nome_fantasia": "ABC Materiais",
        "cnpj": "12345678000195",
        "ie": "123456789",
        "email": "contato@abc.com.br",
        "telefone": "(11) 1234-5678",
        "celular": "(11) 98765-4321",
        "contato_nome": "João Vendedor",
        "endereco": "Avenida Principal",
        "numero": "1000",
        "complemento": "Galpão 5",
        "bairro": "Industrial",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01234567",
        "banco": "Banco do Brasil",
        "agencia": "1234-5",
        "conta": "12345-6",
        "observacoes": "Fornecedor principal de cimento",
        "ativo": true
    }
    ```
    """
    service = FornecedorService(db)
    return await service.criar_fornecedor(fornecedor_data)


@router.get(
    "/{fornecedor_id}",
    response_model=FornecedorResponse,
    summary="Buscar fornecedor por ID",
    description="Retorna os dados de um fornecedor específico",
)
async def get_fornecedor(fornecedor_id: int, db: AsyncSession = Depends(get_db)):
    """Busca um fornecedor por ID"""
    service = FornecedorService(db)
    return await service.buscar_fornecedor(fornecedor_id)


@router.get(
    "/",
    response_model=FornecedorList,
    summary="Listar fornecedores",
    description="Lista todos os fornecedores com paginação e filtros",
)
async def list_fornecedores(
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(False, description="Listar apenas fornecedores ativos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista fornecedores com paginação e filtros.

    **Parâmetros:**
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, lista apenas fornecedores ativos
    """
    service = FornecedorService(db)
    return await service.listar_fornecedores(page, page_size, apenas_ativos)


@router.put(
    "/{fornecedor_id}",
    response_model=FornecedorResponse,
    summary="Atualizar fornecedor",
    description="Atualiza os dados de um fornecedor",
)
async def update_fornecedor(
    fornecedor_id: int,
    fornecedor_data: FornecedorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Atualiza um fornecedor existente.

    **Validações:**
    - Se alterar CNPJ, deve ser único
    - CNPJ deve ser válido
    - E-mail válido (se fornecido)

    **Exemplo de requisição:**
    ```json
    {
        "nome_fantasia": "ABC Materiais Premium",
        "email": "contato.premium@abc.com.br",
        "celular": "(11) 99999-8888"
    }
    ```
    """
    service = FornecedorService(db)
    return await service.atualizar_fornecedor(fornecedor_id, fornecedor_data)


@router.delete(
    "/{fornecedor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Inativar fornecedor",
    description="Inativa um fornecedor (soft delete)",
)
async def delete_fornecedor(fornecedor_id: int, db: AsyncSession = Depends(get_db)):
    """
    Inativa um fornecedor (soft delete).
    O fornecedor não é removido do banco, apenas marcado como inativo.
    """
    service = FornecedorService(db)
    await service.delete_fornecedor(fornecedor_id)
    return None


@router.get(
    "/buscar/search",
    response_model=FornecedorList,
    summary="Buscar fornecedores",
    description="Busca fornecedores por razão social, nome fantasia ou CNPJ",
)
async def search_fornecedores(
    termo: str = Query(..., min_length=1, description="Termo de busca"),
    page: int = Query(1, ge=1, description="Número da página"),
    page_size: int = Query(50, ge=1, le=100, description="Itens por página"),
    apenas_ativos: bool = Query(True, description="Buscar apenas fornecedores ativos"),
    db: AsyncSession = Depends(get_db),
):
    """
    Busca fornecedores por razão social, nome fantasia ou CNPJ.

    **Parâmetros:**
    - **termo**: Termo de busca (busca na razão social, nome fantasia e CNPJ)
    - **page**: Número da página (padrão: 1)
    - **page_size**: Quantidade de itens por página (padrão: 50, máximo: 100)
    - **apenas_ativos**: Se True, busca apenas fornecedores ativos (padrão: True)

    **Exemplo:**
    - `/buscar/search?termo=ABC` - busca fornecedores com "ABC" no nome
    - `/buscar/search?termo=12345678000195` - busca fornecedor com CNPJ "12345678000195"
    """
    service = FornecedorService(db)
    return await service.search_fornecedores(termo, page, page_size, apenas_ativos)
