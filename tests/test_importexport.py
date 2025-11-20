"""
Testes do módulo Import/Export
"""
import pytest
import io
import json
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.modules.importexport.service import ImportExportService
from app.modules.importexport.models import ImportLog, ExportLog, ImportTemplate, ImportStatus, ImportFormat
from app.modules.importexport.schemas import (
    ImportStartRequest,
    ExportRequest,
    ImportTemplateCreate,
    ImportFormatEnum,
    ExportFormatEnum
)
from app.core.database import Base


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def db_session():
    """Fixture de banco de dados SQLite in-memory"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def csv_file_content():
    """Conteúdo de arquivo CSV de exemplo"""
    return """codigo,descricao,preco_venda
PROD001,Produto 1,100.50
PROD002,Produto 2,200.00
PROD003,Produto 3,150.75"""


@pytest.fixture
def json_file_content():
    """Conteúdo de arquivo JSON de exemplo"""
    return json.dumps([
        {"codigo": "PROD001", "descricao": "Produto 1", "preco_venda": 100.50},
        {"codigo": "PROD002", "descricao": "Produto 2", "preco_venda": 200.00},
        {"codigo": "PROD003", "descricao": "Produto 3", "preco_venda": 150.75}
    ])


# ============================================================================
# TESTES DE LEITURA DE ARQUIVOS
# ============================================================================

@pytest.mark.asyncio
async def test_read_csv(db_session, csv_file_content):
    """Teste de leitura de arquivo CSV"""
    service = ImportExportService(db_session)

    file = io.BytesIO(csv_file_content.encode('utf-8'))
    data = service._read_csv(file)

    assert len(data) == 3
    assert data[0]["codigo"] == "PROD001"
    assert data[0]["descricao"] == "Produto 1"
    assert data[0]["preco_venda"] == "100.50"


@pytest.mark.asyncio
async def test_read_json(db_session, json_file_content):
    """Teste de leitura de arquivo JSON"""
    service = ImportExportService(db_session)

    file = io.BytesIO(json_file_content.encode('utf-8'))
    data = service._read_json(file)

    assert len(data) == 3
    assert data[0]["codigo"] == "PROD001"
    assert data[1]["preco_venda"] == 200.00


# ============================================================================
# TESTES DE PREVIEW
# ============================================================================

@pytest.mark.asyncio
async def test_preview_import_csv(db_session, csv_file_content):
    """Teste de preview de importação CSV"""
    service = ImportExportService(db_session)

    file = io.BytesIO(csv_file_content.encode('utf-8'))

    preview = await service.preview_import(
        file,
        ImportFormat.CSV,
        "produtos",
        sample_size=3
    )

    assert preview.total_rows == 3
    assert len(preview.sample_rows) == 3
    assert "codigo" in preview.columns
    assert "descricao" in preview.columns
    assert preview.detected_format == ImportFormat.CSV


@pytest.mark.asyncio
async def test_preview_import_with_suggestions(db_session, csv_file_content):
    """Teste de sugestões de mapeamento"""
    service = ImportExportService(db_session)

    file = io.BytesIO(csv_file_content.encode('utf-8'))

    preview = await service.preview_import(
        file,
        ImportFormat.CSV,
        "produtos"
    )

    # Deve sugerir mapeamentos
    assert len(preview.mapping_suggestions) > 0
    assert preview.mapping_suggestions.get("codigo") == "codigo"
    assert preview.mapping_suggestions.get("descricao") == "descricao"


# ============================================================================
# TESTES DE VALIDAÇÃO
# ============================================================================

@pytest.mark.asyncio
async def test_validate_import_success(db_session, csv_file_content):
    """Teste de validação bem-sucedida"""
    service = ImportExportService(db_session)

    file = io.BytesIO(csv_file_content.encode('utf-8'))

    mapping = {
        "codigo": "codigo",
        "descricao": "descricao",
        "preco_venda": "preco_venda"
    }

    errors = await service.validate_import(
        file,
        ImportFormat.CSV,
        "produtos",
        mapping
    )

    # Não deve haver erros críticos
    assert isinstance(errors, list)


@pytest.mark.asyncio
async def test_validate_import_missing_required_field(db_session):
    """Teste de validação com campo obrigatório faltando"""
    service = ImportExportService(db_session)

    # CSV sem campo obrigatório
    content = """nome
Produto Sem Codigo"""

    file = io.BytesIO(content.encode('utf-8'))

    mapping = {"nome": "descricao"}

    errors = await service.validate_import(
        file,
        ImportFormat.CSV,
        "produtos",
        mapping
    )

    # Deve haver erros de campos obrigatórios
    assert len(errors) > 0
    assert any("codigo" in str(e.error).lower() for e in errors)


# ============================================================================
# TESTES DE IMPORT LOG
# ============================================================================

@pytest.mark.asyncio
async def test_create_import_log(db_session):
    """Teste de criação de log de importação"""
    service = ImportExportService(db_session)

    log_data = {
        "module": "produtos",
        "format": ImportFormat.CSV,
        "filename": "test.csv",
        "status": ImportStatus.PENDING
    }

    log = await service.repository.create_import_log(log_data)

    assert log.id is not None
    assert log.module == "produtos"
    assert log.filename == "test.csv"
    assert log.status == ImportStatus.PENDING


@pytest.mark.asyncio
async def test_get_import_status(db_session):
    """Teste de consulta de status de importação"""
    service = ImportExportService(db_session)

    # Criar log
    log = await service.repository.create_import_log({
        "module": "produtos",
        "format": ImportFormat.CSV,
        "filename": "test.csv",
        "status": ImportStatus.PENDING,
        "total_rows": 10,
        "processed_rows": 5
    })

    # Consultar status
    status = await service.get_import_status(log.id)

    assert status.id == log.id
    assert status.total_rows == 10
    assert status.processed_rows == 5
    assert status.progress_percentage == 50.0


# ============================================================================
# TESTES DE EXPORT
# ============================================================================

@pytest.mark.asyncio
async def test_write_csv(db_session, tmp_path):
    """Teste de escrita de arquivo CSV"""
    service = ImportExportService(db_session)

    data = [
        {"codigo": "PROD001", "nome": "Produto 1", "preco": 100.0},
        {"codigo": "PROD002", "nome": "Produto 2", "preco": 200.0}
    ]

    file_path = str(tmp_path / "test.csv")
    service._write_csv(data, file_path, include_headers=True)

    # Verificar se arquivo foi criado
    with open(file_path, 'r') as f:
        content = f.read()

    assert "codigo" in content
    assert "PROD001" in content
    assert "Produto 1" in content


@pytest.mark.asyncio
async def test_write_json(db_session, tmp_path):
    """Teste de escrita de arquivo JSON"""
    service = ImportExportService(db_session)

    data = [
        {"codigo": "PROD001", "nome": "Produto 1"},
        {"codigo": "PROD002", "nome": "Produto 2"}
    ]

    file_path = str(tmp_path / "test.json")
    service._write_json(data, file_path)

    # Verificar se arquivo foi criado
    with open(file_path, 'r') as f:
        loaded_data = json.load(f)

    assert len(loaded_data) == 2
    assert loaded_data[0]["codigo"] == "PROD001"


# ============================================================================
# TESTES DE TEMPLATES
# ============================================================================

@pytest.mark.asyncio
async def test_create_template(db_session):
    """Teste de criação de template"""
    service = ImportExportService(db_session)

    template_data = ImportTemplateCreate(
        name="Template Produtos Padrão",
        module="produtos",
        description="Template padrão para importação de produtos",
        format=ImportFormatEnum.CSV,
        column_mapping={
            "Código": "codigo",
            "Descrição": "descricao",
            "Preço": "preco_venda"
        },
        required_columns=["codigo", "descricao", "preco_venda"]
    )

    template = await service.create_template(template_data)

    assert template.id is not None
    assert template.name == "Template Produtos Padrão"
    assert template.module == "produtos"


@pytest.mark.asyncio
async def test_list_templates(db_session):
    """Teste de listagem de templates"""
    service = ImportExportService(db_session)

    # Criar alguns templates
    for i in range(3):
        await service.create_template(ImportTemplateCreate(
            name=f"Template {i}",
            module="produtos",
            format=ImportFormatEnum.CSV,
            column_mapping={"col": "field"},
            required_columns=["field"]
        ))

    # Listar
    templates = await service.list_templates(module="produtos")

    assert len(templates) == 3


@pytest.mark.asyncio
async def test_create_duplicate_template_fails(db_session):
    """Teste que template duplicado falha"""
    from app.core.exceptions import BusinessException

    service = ImportExportService(db_session)

    template_data = ImportTemplateCreate(
        name="Template Único",
        module="produtos",
        format=ImportFormatEnum.CSV,
        column_mapping={"col": "field"},
        required_columns=["field"]
    )

    # Criar primeiro
    await service.create_template(template_data)

    # Tentar criar duplicado
    with pytest.raises(BusinessException) as exc_info:
        await service.create_template(template_data)

    assert "já existe" in str(exc_info.value)


# ============================================================================
# TESTES DE ESTATÍSTICAS
# ============================================================================

@pytest.mark.asyncio
async def test_get_statistics(db_session):
    """Teste de estatísticas"""
    service = ImportExportService(db_session)

    # Criar alguns logs
    await service.repository.create_import_log({
        "module": "produtos",
        "format": ImportFormat.CSV,
        "filename": "test1.csv",
        "status": ImportStatus.COMPLETED
    })

    await service.repository.create_import_log({
        "module": "clientes",
        "format": ImportFormat.EXCEL,
        "filename": "test2.xlsx",
        "status": ImportStatus.FAILED
    })

    # Obter estatísticas
    stats = await service.get_statistics()

    assert stats.total_imports == 2
    assert stats.successful_imports == 1
    assert stats.failed_imports == 1


# ============================================================================
# TESTES DE HELPERS
# ============================================================================

@pytest.mark.asyncio
async def test_suggest_column_mapping(db_session):
    """Teste de sugestão de mapeamento de colunas"""
    service = ImportExportService(db_session)

    columns = ["Código", "Descrição", "Preço"]
    suggestions = service._suggest_column_mapping(columns, "produtos")

    # Deve sugerir mapeamentos corretos
    assert "Código" in suggestions or "Descrição" in suggestions


@pytest.mark.asyncio
async def test_get_required_fields(db_session):
    """Teste de campos obrigatórios por módulo"""
    service = ImportExportService(db_session)

    required = service._get_required_fields("produtos")

    assert "codigo" in required
    assert "descricao" in required
    assert "preco_venda" in required


# ============================================================================
# TESTES DE EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_preview_empty_file(db_session):
    """Teste de preview com arquivo vazio"""
    from app.core.exceptions import BusinessException

    service = ImportExportService(db_session)

    file = io.BytesIO(b"")

    with pytest.raises(BusinessException) as exc_info:
        await service.preview_import(file, ImportFormat.CSV, "produtos")

    assert "vazio" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_import_status_not_found(db_session):
    """Teste de status de importação inexistente"""
    from app.core.exceptions import NotFoundException

    service = ImportExportService(db_session)

    with pytest.raises(NotFoundException):
        await service.get_import_status(99999)


# ============================================================================
# TESTES DE INTEGRAÇÃO
# ============================================================================

@pytest.mark.asyncio
async def test_full_import_flow_dry_run(db_session, csv_file_content):
    """Teste de fluxo completo de importação em dry run"""
    service = ImportExportService(db_session)

    # Preparar arquivo
    file = io.BytesIO(csv_file_content.encode('utf-8'))

    # Criar request
    request = ImportStartRequest(
        module="produtos",
        format=ImportFormatEnum.CSV,
        mapping={
            "codigo": "codigo",
            "descricao": "descricao",
            "preco_venda": "preco_venda"
        },
        skip_errors=False,
        dry_run=True  # Não persistir dados
    )

    # Executar importação
    status = await service.start_import(file, "test.csv", request, user_id=1)

    # Verificar resultado
    assert status.id is not None
    assert status.status == ImportStatus.COMPLETED
    assert status.total_rows == 3
    assert status.success_rows == 3
    assert status.failed_rows == 0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.skip(reason="Performance test - executar manualmente")
async def test_import_large_file_performance(db_session):
    """Teste de performance com arquivo grande"""
    service = ImportExportService(db_session)

    # Gerar CSV grande (10000 linhas)
    lines = ["codigo,descricao,preco_venda"]
    for i in range(10000):
        lines.append(f"PROD{i:05d},Produto {i},{100.0 + i}")

    content = "\n".join(lines)
    file = io.BytesIO(content.encode('utf-8'))

    import time
    start = time.time()

    preview = await service.preview_import(
        file,
        ImportFormat.CSV,
        "produtos",
        sample_size=100
    )

    duration = time.time() - start

    assert preview.total_rows == 10000
    assert duration < 5.0  # Deve completar em menos de 5 segundos
