"""
Repository de Import/Export
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .models import ImportLog, ExportLog, ImportTemplate, ImportStatus, ExportStatus


class ImportExportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # IMPORT LOG
    # ========================================================================

    async def create_import_log(self, data: Dict[str, Any]) -> ImportLog:
        """Criar log de importação"""
        import_log = ImportLog(**data)
        self.db.add(import_log)
        await self.db.commit()
        await self.db.refresh(import_log)
        return import_log

    async def get_import_log(self, import_id: int) -> Optional[ImportLog]:
        """Buscar log de importação"""
        result = await self.db.execute(
            select(ImportLog).where(ImportLog.id == import_id)
        )
        return result.scalar_one_or_none()

    async def update_import_log(
        self,
        import_id: int,
        data: Dict[str, Any]
    ) -> Optional[ImportLog]:
        """Atualizar log de importação"""
        import_log = await self.get_import_log(import_id)
        if not import_log:
            return None

        for key, value in data.items():
            if hasattr(import_log, key):
                setattr(import_log, key, value)

        await self.db.commit()
        await self.db.refresh(import_log)
        return import_log

    async def list_import_logs(
        self,
        module: Optional[str] = None,
        status: Optional[ImportStatus] = None,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportLog]:
        """Listar logs de importação"""
        query = select(ImportLog)

        filters = []
        if module:
            filters.append(ImportLog.module == module)
        if status:
            filters.append(ImportLog.status == status)
        if user_id:
            filters.append(ImportLog.user_id == user_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(ImportLog.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_imports(
        self,
        module: Optional[str] = None,
        status: Optional[ImportStatus] = None
    ) -> int:
        """Contar importações"""
        query = select(func.count(ImportLog.id))

        filters = []
        if module:
            filters.append(ImportLog.module == module)
        if status:
            filters.append(ImportLog.status == status)

        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        return result.scalar() or 0

    # ========================================================================
    # EXPORT LOG
    # ========================================================================

    async def create_export_log(self, data: Dict[str, Any]) -> ExportLog:
        """Criar log de exportação"""
        export_log = ExportLog(**data)
        self.db.add(export_log)
        await self.db.commit()
        await self.db.refresh(export_log)
        return export_log

    async def get_export_log(self, export_id: int) -> Optional[ExportLog]:
        """Buscar log de exportação"""
        result = await self.db.execute(
            select(ExportLog).where(ExportLog.id == export_id)
        )
        return result.scalar_one_or_none()

    async def update_export_log(
        self,
        export_id: int,
        data: Dict[str, Any]
    ) -> Optional[ExportLog]:
        """Atualizar log de exportação"""
        export_log = await self.get_export_log(export_id)
        if not export_log:
            return None

        for key, value in data.items():
            if hasattr(export_log, key):
                setattr(export_log, key, value)

        await self.db.commit()
        await self.db.refresh(export_log)
        return export_log

    async def list_export_logs(
        self,
        module: Optional[str] = None,
        status: Optional[ExportStatus] = None,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExportLog]:
        """Listar logs de exportação"""
        query = select(ExportLog)

        filters = []
        if module:
            filters.append(ExportLog.module == module)
        if status:
            filters.append(ExportLog.status == status)
        if user_id:
            filters.append(ExportLog.user_id == user_id)

        if filters:
            query = query.where(and_(*filters))

        query = query.order_by(desc(ExportLog.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ========================================================================
    # TEMPLATES
    # ========================================================================

    async def create_template(self, data: Dict[str, Any]) -> ImportTemplate:
        """Criar template"""
        template = ImportTemplate(**data)
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def get_template(self, template_id: int) -> Optional[ImportTemplate]:
        """Buscar template"""
        result = await self.db.execute(
            select(ImportTemplate).where(ImportTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_template_by_name(
        self,
        name: str,
        module: str
    ) -> Optional[ImportTemplate]:
        """Buscar template por nome e módulo"""
        result = await self.db.execute(
            select(ImportTemplate).where(
                and_(
                    ImportTemplate.name == name,
                    ImportTemplate.module == module
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        module: Optional[str] = None,
        is_active: bool = True,
        skip: int = 0,
        limit: int = 100
    ) -> List[ImportTemplate]:
        """Listar templates"""
        query = select(ImportTemplate)

        filters = [ImportTemplate.is_active == is_active]
        if module:
            filters.append(ImportTemplate.module == module)

        query = query.where(and_(*filters)).order_by(ImportTemplate.name)
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_template(
        self,
        template_id: int,
        data: Dict[str, Any]
    ) -> Optional[ImportTemplate]:
        """Atualizar template"""
        template = await self.get_template(template_id)
        if not template:
            return None

        for key, value in data.items():
            if hasattr(template, key) and key != "id":
                setattr(template, key, value)

        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete_template(self, template_id: int) -> bool:
        """Deletar template (soft delete)"""
        template = await self.get_template(template_id)
        if not template or template.is_system:
            return False

        template.is_active = False
        await self.db.commit()
        return True

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_import_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Estatísticas de importações"""
        query = select(
            func.count(ImportLog.id).label("total"),
            func.count(
                ImportLog.id
            ).filter(ImportLog.status == ImportStatus.COMPLETED).label("successful"),
            func.count(
                ImportLog.id
            ).filter(ImportLog.status == ImportStatus.FAILED).label("failed")
        )

        filters = []
        if start_date:
            filters.append(ImportLog.created_at >= start_date)
        if end_date:
            filters.append(ImportLog.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        row = result.first()

        return {
            "total": row.total if row else 0,
            "successful": row.successful if row else 0,
            "failed": row.failed if row else 0
        }

    async def get_export_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Estatísticas de exportações"""
        query = select(
            func.count(ExportLog.id).label("total"),
            func.count(
                ExportLog.id
            ).filter(ExportLog.status == ExportStatus.COMPLETED).label("successful"),
            func.count(
                ExportLog.id
            ).filter(ExportLog.status == ExportStatus.FAILED).label("failed")
        )

        filters = []
        if start_date:
            filters.append(ExportLog.created_at >= start_date)
        if end_date:
            filters.append(ExportLog.created_at <= end_date)

        if filters:
            query = query.where(and_(*filters))

        result = await self.db.execute(query)
        row = result.first()

        return {
            "total": row.total if row else 0,
            "successful": row.successful if row else 0,
            "failed": row.failed if row else 0
        }

    async def get_most_imported_module(self) -> Optional[str]:
        """Módulo mais importado"""
        result = await self.db.execute(
            select(ImportLog.module, func.count(ImportLog.id).label("count"))
            .group_by(ImportLog.module)
            .order_by(desc("count"))
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    async def get_most_exported_module(self) -> Optional[str]:
        """Módulo mais exportado"""
        result = await self.db.execute(
            select(ExportLog.module, func.count(ExportLog.id).label("count"))
            .group_by(ExportLog.module)
            .order_by(desc("count"))
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None
