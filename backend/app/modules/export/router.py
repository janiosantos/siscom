"""
Router para endpoints de exportação
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User

from .service import ExportService
from .schemas import (
    DashboardExportRequest,
    OrcamentosExportRequest,
    VendasExportRequest,
    ProdutosExportRequest
)

router = APIRouter()


@router.post(
    "/dashboard",
    summary="Exportar dados do dashboard",
    description="Exporta dados do dashboard em Excel ou CSV"
)
async def export_dashboard(
    request: DashboardExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exportar dados do dashboard

    - **formato**: 'excel' ou 'csv'
    - **tipo**: Tipo de dados (stats, vendas_dia, produtos, vendedores, status)
    - **filtros**: Filtros opcionais (datas, vendedor, cliente, etc)

    Retorna arquivo Excel ou CSV para download
    """
    try:
        service = ExportService(db)
        file_content = await service.export_dashboard_stats(
            formato=request.formato,
            tipo=request.tipo,
            filtros=request.filtros
        )

        # Definir tipo de conteúdo e nome do arquivo
        if request.formato == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        else:
            media_type = "text/csv"
            extension = "csv"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dashboard_{request.tipo}_{timestamp}.{extension}"

        return StreamingResponse(
            file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependência não instalada: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar export: {str(e)}"
        )


@router.post(
    "/orcamentos",
    summary="Exportar orçamentos",
    description="Exporta orçamentos em Excel ou CSV (bulk export)"
)
async def export_orcamentos(
    request: OrcamentosExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exportar orçamentos em bulk

    - **formato**: 'excel' ou 'csv'
    - **filtros**: Filtros opcionais (datas, cliente, status)
    - **ids**: Lista de IDs específicos (opcional)

    Retorna arquivo Excel ou CSV com todos os orçamentos filtrados
    """
    try:
        service = ExportService(db)
        file_content = await service.export_orcamentos(
            formato=request.formato,
            filtros=request.filtros,
            ids=request.ids
        )

        if request.formato == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        else:
            media_type = "text/csv"
            extension = "csv"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orcamentos_{timestamp}.{extension}"

        return StreamingResponse(
            file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependência não instalada: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar export: {str(e)}"
        )


@router.post(
    "/vendas",
    summary="Exportar vendas",
    description="Exporta vendas em Excel ou CSV (bulk export)"
)
async def export_vendas(
    request: VendasExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exportar vendas em bulk

    - **formato**: 'excel' ou 'csv'
    - **filtros**: Filtros opcionais (datas, vendedor, cliente, status)
    - **ids**: Lista de IDs específicos (opcional)

    Retorna arquivo Excel ou CSV com todas as vendas filtradas
    """
    try:
        service = ExportService(db)
        file_content = await service.export_vendas(
            formato=request.formato,
            filtros=request.filtros,
            ids=request.ids
        )

        if request.formato == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        else:
            media_type = "text/csv"
            extension = "csv"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"vendas_{timestamp}.{extension}"

        return StreamingResponse(
            file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependência não instalada: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar export: {str(e)}"
        )


@router.post(
    "/produtos",
    summary="Exportar produtos",
    description="Exporta produtos em Excel ou CSV"
)
async def export_produtos(
    request: ProdutosExportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exportar produtos

    - **formato**: 'excel' ou 'csv'
    - **categoria_id**: Filtrar por categoria (opcional)
    - **apenas_ativos**: Apenas produtos ativos (padrão: true)

    Retorna arquivo Excel ou CSV com todos os produtos
    """
    try:
        service = ExportService(db)
        file_content = await service.export_produtos(
            formato=request.formato,
            categoria_id=request.categoria_id,
            apenas_ativos=request.apenas_ativos
        )

        if request.formato == "excel":
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = "xlsx"
        else:
            media_type = "text/csv"
            extension = "csv"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"produtos_{timestamp}.{extension}"

        return StreamingResponse(
            file_content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dependência não instalada: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar export: {str(e)}"
        )
