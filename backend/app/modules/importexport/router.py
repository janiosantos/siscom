"""
Router de Import/Export
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import json

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user, require_permission
from app.modules.auth.models import User

from .service import ImportExportService
from .schemas import (
    ImportPreviewResponse,
    ImportStartRequest,
    ImportStatusResponse,
    ImportRollbackRequest,
    ExportRequest,
    ExportStatusResponse,
    ImportTemplateCreate,
    ImportTemplateResponse,
    ImportTemplateListResponse,
    ImportExportStats,
    ImportFormatEnum,
    ExportFormatEnum
)

router = APIRouter()


# ============================================================================
# IMPORT ENDPOINTS
# ============================================================================

@router.post(
    "/import/preview",
    response_model=ImportPreviewResponse,
    summary="Preview de importação",
    description="Gera preview da importação com validação básica",
    status_code=status.HTTP_200_OK
)
async def preview_import(
    file: UploadFile = File(..., description="Arquivo para importar"),
    format: ImportFormatEnum = Form(..., description="Formato do arquivo"),
    module: str = Form(..., description="Módulo alvo (produtos, clientes, etc)"),
    sample_size: int = Form(10, description="Quantidade de linhas para preview"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.preview"))
):
    """
    Preview de importação com validação

    Permite visualizar uma amostra dos dados antes de importar,
    com sugestões de mapeamento de colunas e validação básica.

    **Formatos suportados**: CSV, Excel, JSON
    """
    service = ImportExportService(db)
    return await service.preview_import(
        file.file,
        format,
        module,
        sample_size
    )


@router.post(
    "/import/start",
    response_model=ImportStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar importação",
    description="Inicia o processo de importação de dados"
)
async def start_import(
    file: UploadFile = File(...),
    request_json: str = Form(..., description="JSON do ImportStartRequest"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.import"))
):
    """
    Iniciar importação de dados

    O processo é assíncrono. Use o endpoint `/import/status/{import_id}`
    para acompanhar o progresso.

    **Exemplo de request_json**:
    ```json
    {
        "module": "produtos",
        "format": "csv",
        "mapping": {
            "Código": "codigo",
            "Descrição": "descricao",
            "Preço": "preco_venda"
        },
        "skip_errors": false,
        "dry_run": false
    }
    ```
    """
    request = ImportStartRequest.model_validate_json(request_json)
    service = ImportExportService(db)

    return await service.start_import(
        file.file,
        file.filename,
        request,
        current_user.id
    )


@router.get(
    "/import/status/{import_id}",
    response_model=ImportStatusResponse,
    summary="Status da importação",
    description="Consultar status e progresso da importação"
)
async def get_import_status(
    import_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consultar status da importação

    Retorna informações detalhadas incluindo:
    - Progresso (linhas processadas)
    - Estatísticas (sucesso/falhas)
    - Erros de validação/importação
    - Possibilidade de rollback
    """
    service = ImportExportService(db)
    return await service.get_import_status(import_id)


@router.post(
    "/import/{import_id}/rollback",
    response_model=ImportStatusResponse,
    summary="Rollback de importação",
    description="Reverte uma importação, deletando todos os registros criados"
)
async def rollback_import(
    import_id: int,
    request: ImportRollbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.rollback"))
):
    """
    Fazer rollback de importação

    **ATENÇÃO**: Esta operação deleta todos os registros criados
    pela importação. Use com cautela!

    Apenas importações com status `completed` podem ser revertidas.
    """
    service = ImportExportService(db)
    return await service.rollback_import(import_id, request.reason)


@router.get(
    "/import/history",
    response_model=List[ImportStatusResponse],
    summary="Histórico de importações",
    description="Lista todas as importações realizadas"
)
async def list_imports(
    module: Optional[str] = Query(None, description="Filtrar por módulo"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Histórico de importações

    Retorna lista de todas as importações com filtros opcionais.
    """
    service = ImportExportService(db)
    imports = await service.repository.list_import_logs(
        module=module,
        status=status,
        user_id=current_user.id if not current_user.is_admin else None,
        skip=skip,
        limit=limit
    )
    return [ImportStatusResponse.model_validate(i) for i in imports]


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@router.post(
    "/export/start",
    response_model=ExportStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar exportação",
    description="Inicia o processo de exportação de dados"
)
async def start_export(
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.export"))
):
    """
    Iniciar exportação de dados

    Suporta exportação em múltiplos formatos com filtros opcionais.

    **Exemplo**:
    ```json
    {
        "module": "produtos",
        "format": "excel",
        "filters": {
            "categoria_id": 1,
            "ativo": true
        },
        "columns": ["codigo", "descricao", "preco_venda"],
        "include_headers": true,
        "filename": "produtos_2025.xlsx"
    }
    ```
    """
    service = ImportExportService(db)
    return await service.start_export(request, current_user.id)


@router.get(
    "/export/status/{export_id}",
    response_model=ExportStatusResponse,
    summary="Status da exportação",
    description="Consultar status da exportação"
)
async def get_export_status(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consultar status da exportação

    Retorna informações sobre a exportação incluindo caminho do arquivo gerado.
    """
    service = ImportExportService(db)
    export_log = await service.repository.get_export_log(export_id)

    if not export_log:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Exportação {export_id} não encontrada")

    return ExportStatusResponse.model_validate(export_log)


@router.get(
    "/export/{export_id}/download",
    summary="Download do arquivo exportado",
    description="Fazer download do arquivo gerado pela exportação"
)
async def download_export(
    export_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download do arquivo exportado

    Retorna o arquivo gerado pela exportação.
    """
    service = ImportExportService(db)
    export_log = await service.repository.get_export_log(export_id)

    if not export_log:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Exportação {export_id} não encontrada")

    if not export_log.file_path:
        from app.core.exceptions import BusinessException
        raise BusinessException("Arquivo não disponível para download")

    return FileResponse(
        export_log.file_path,
        media_type="application/octet-stream",
        filename=export_log.filename
    )


@router.get(
    "/export/history",
    response_model=List[ExportStatusResponse],
    summary="Histórico de exportações",
    description="Lista todas as exportações realizadas"
)
async def list_exports(
    module: Optional[str] = Query(None, description="Filtrar por módulo"),
    status: Optional[str] = Query(None, description="Filtrar por status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Histórico de exportações

    Retorna lista de todas as exportações com filtros opcionais.
    """
    service = ImportExportService(db)
    exports = await service.repository.list_export_logs(
        module=module,
        status=status,
        user_id=current_user.id if not current_user.is_admin else None,
        skip=skip,
        limit=limit
    )
    return [ExportStatusResponse.model_validate(e) for e in exports]


# ============================================================================
# TEMPLATES
# ============================================================================

@router.post(
    "/templates",
    response_model=ImportTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar template de importação",
    description="Cria template pré-configurado para importações recorrentes"
)
async def create_template(
    request: ImportTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.manage_templates"))
):
    """
    Criar template de importação

    Templates permitem salvar configurações de importação para reutilização,
    incluindo mapeamento de colunas e regras de validação.
    """
    service = ImportExportService(db)
    return await service.create_template(request, current_user.id)


@router.get(
    "/templates",
    response_model=List[ImportTemplateResponse],
    summary="Listar templates",
    description="Lista todos os templates disponíveis"
)
async def list_templates(
    module: Optional[str] = Query(None, description="Filtrar por módulo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Listar templates de importação

    Retorna lista de templates disponíveis, opcionalmente filtrados por módulo.
    """
    service = ImportExportService(db)
    return await service.list_templates(module, skip, limit)


@router.get(
    "/templates/{template_id}",
    response_model=ImportTemplateResponse,
    summary="Obter template por ID",
    description="Retorna detalhes de um template específico"
)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obter template por ID
    """
    service = ImportExportService(db)
    template = await service.repository.get_template(template_id)

    if not template:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Template {template_id} não encontrado")

    return ImportTemplateResponse.model_validate(template)


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deletar template",
    description="Remove um template (soft delete)"
)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("importexport.manage_templates"))
):
    """
    Deletar template

    Templates do sistema não podem ser deletados.
    """
    service = ImportExportService(db)
    success = await service.repository.delete_template(template_id)

    if not success:
        from app.core.exceptions import BusinessException
        raise BusinessException("Template não pode ser deletado")


# ============================================================================
# STATISTICS
# ============================================================================

@router.get(
    "/statistics",
    response_model=ImportExportStats,
    summary="Estatísticas de import/export",
    description="Retorna estatísticas gerais de importações e exportações"
)
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Estatísticas de import/export

    Retorna métricas consolidadas de todas as operações de import/export,
    incluindo:
    - Total de importações/exportações
    - Taxa de sucesso/falha
    - Módulos mais utilizados
    """
    service = ImportExportService(db)
    return await service.get_statistics()


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Verifica se o módulo está funcionando"
)
async def health_check():
    """
    Health check do módulo Import/Export
    """
    return {
        "status": "healthy",
        "module": "importexport",
        "features": {
            "import": ["csv", "excel", "json"],
            "export": ["csv", "excel", "json", "pdf"],
            "templates": True,
            "rollback": True,
            "preview": True
        }
    }
