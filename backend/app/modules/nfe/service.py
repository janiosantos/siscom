"""
Service Layer para Notas Fiscais
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import math
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.nfe.repository import NotaFiscalRepository
from app.modules.nfe.models import TipoNota, StatusNota
from app.modules.nfe.schemas import (
    NotaFiscalCreate,
    NotaFiscalResponse,
    NotaFiscalList,
    ImportarXMLCreate,
    EmitirNFCeCreate,
    ConsultarNotaResponse,
    TipoNotaEnum,
    StatusNotaEnum,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.produtos.schemas import ProdutoCreate, ProdutoUpdate
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.schemas import EntradaEstoqueCreate
from app.utils.xml_reader import NFeXMLReader
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class NotaFiscalService:
    """Service para regras de negócio de Notas Fiscais"""

    def __init__(self, session: AsyncSession):
        self.repository = NotaFiscalRepository(session)
        self.produto_repository = ProdutoRepository(session)
        self.estoque_service = EstoqueService(session)
        self.session = session

    async def importar_xml_nfe(
        self, importar_data: ImportarXMLCreate
    ) -> NotaFiscalResponse:
        """
        Importa XML de NF-e e processa:
        1. Lê XML com NFeXMLReader
        2. Cria/atualiza produtos
        3. Registra entrada de estoque
        4. Cria conta a pagar (TODO: quando módulo financeiro estiver disponível)

        Args:
            importar_data: Dados para importação

        Returns:
            NotaFiscalResponse com a nota criada

        Raises:
            ValidationException: Se XML inválido ou chave duplicada
        """
        # 1. Extrai dados do XML
        try:
            dados_xml = NFeXMLReader.extract_nfe_data(importar_data.xml_content)
        except Exception as e:
            raise ValidationException(f"Erro ao processar XML: {str(e)}")

        # Valida se nota já existe
        chave_acesso = dados_xml["nota"]["chave"]
        nota_existente = await self.repository.get_by_chave(chave_acesso)
        if nota_existente:
            raise ValidationException(
                f"Nota fiscal com chave {chave_acesso} já foi importada"
            )

        # 2. Cria a nota fiscal
        nota_data = NotaFiscalCreate(
            tipo=TipoNotaEnum.NFE,
            numero=str(dados_xml["nota"]["numero"]),
            serie=str(dados_xml["nota"]["serie"]),
            chave_acesso=chave_acesso,
            data_emissao=datetime.fromisoformat(
                dados_xml["nota"]["data_emissao"].replace("Z", "+00:00")
            ),
            fornecedor_id=None,  # TODO: Buscar/criar fornecedor
            valor_produtos=float(dados_xml["totais"]["valor_produtos"]),
            valor_total=float(dados_xml["totais"]["valor_total"]),
            valor_icms=float(dados_xml["totais"]["valor_icms"]),
            valor_ipi=float(dados_xml["totais"]["valor_ipi"]),
            status=StatusNotaEnum.AUTORIZADA,  # XML importado já está autorizado
            xml_nfe=importar_data.xml_content,
            observacoes=f"Importado via XML - Fornecedor: {dados_xml['fornecedor']['razao_social']}",
        )

        nota = await self.repository.create(nota_data)

        # 3. Processa produtos e estoque
        if importar_data.registrar_entrada_estoque:
            await self._processar_produtos_e_estoque(dados_xml["produtos"], nota.id)

        # 4. TODO: Criar conta a pagar quando módulo financeiro estiver disponível
        # if importar_data.criar_conta_pagar:
        #     await self._criar_conta_pagar(nota, dados_xml)

        await self.session.flush()
        await self.session.refresh(nota)

        return NotaFiscalResponse.model_validate(nota)

    async def _processar_produtos_e_estoque(
        self, produtos_xml: List[dict], nota_id: int
    ):
        """
        Cria/atualiza produtos e registra entrada de estoque

        Args:
            produtos_xml: Lista de produtos do XML
            nota_id: ID da nota fiscal
        """
        for item_xml in produtos_xml:
            # Tenta encontrar produto por código de barras (EAN) ou código
            codigo_barras = item_xml["ean"] or item_xml["codigo"]
            if not codigo_barras or codigo_barras == "SEM GTIN":
                codigo_barras = f"COD-{item_xml['codigo']}"

            produto = await self.produto_repository.get_by_codigo_barras(codigo_barras)

            # Se produto não existe, cria
            if not produto:
                # TODO: Buscar categoria padrão ou criar categoria "Importados"
                # Por enquanto, vamos assumir categoria_id = 1
                produto_data = ProdutoCreate(
                    codigo_barras=codigo_barras,
                    descricao=item_xml["descricao"][:200],  # Limita a 200 caracteres
                    categoria_id=1,  # TODO: Melhorar lógica de categoria
                    preco_custo=float(item_xml["valor_unitario"]),
                    preco_venda=float(item_xml["valor_unitario"])
                    * 1.3,  # Margem 30%
                    estoque_atual=0.0,
                    estoque_minimo=0.0,
                    unidade=item_xml["unidade"] or "UN",
                    ncm=item_xml["ncm"] if item_xml["ncm"] else None,
                    ativo=True,
                )

                try:
                    produto = await self.produto_repository.create(produto_data)
                except Exception as e:
                    # Se falhar ao criar produto, tenta usar código alternativo
                    produto_data.codigo_barras = f"NF-{nota_id}-{item_xml['codigo']}"
                    produto = await self.produto_repository.create(produto_data)
            else:
                # Atualiza produto existente (preço de custo e NCM)
                update_data = ProdutoUpdate(
                    preco_custo=float(item_xml["valor_unitario"]),
                    ncm=item_xml["ncm"] if item_xml["ncm"] else produto.ncm,
                )
                produto = await self.produto_repository.update(produto.id, update_data)

            # Registra entrada de estoque
            entrada_data = EntradaEstoqueCreate(
                produto_id=produto.id,
                quantidade=float(item_xml["quantidade"]),
                custo_unitario=float(item_xml["valor_unitario"]),
                documento_referencia=f"NF-e {nota_id}",
                observacao=f"Importação de NF-e - {item_xml['descricao'][:100]}",
                usuario_id=1,  # TODO: Pegar usuário da sessão
            )

            await self.estoque_service.entrada_estoque(entrada_data)

    async def emitir_nfce(self, emissao_data: EmitirNFCeCreate) -> NotaFiscalResponse:
        """
        Emite NFC-e para uma venda (simulado)

        Esta é uma implementação simulada que apenas cria o registro da nota.
        Em produção, integraria com a SEFAZ para emissão real.

        Args:
            emissao_data: Dados para emissão

        Returns:
            NotaFiscalResponse com a nota criada

        Raises:
            NotFoundException: Se venda não encontrada
            ValidationException: Se venda já possui NFC-e
        """
        # TODO: Buscar dados da venda quando módulo vendas estiver completo
        # Por enquanto, cria uma nota simulada

        # Gera chave de acesso simulada (44 dígitos)
        chave_simulada = self._gerar_chave_simulada()

        # Cria nota fiscal
        nota_data = NotaFiscalCreate(
            tipo=TipoNotaEnum.NFCE,
            numero=str(datetime.now().timestamp())[:10],  # Número simulado
            serie=emissao_data.serie,
            chave_acesso=chave_simulada,
            data_emissao=datetime.now(),
            venda_id=emissao_data.venda_id,
            valor_produtos=0.0,  # TODO: Buscar da venda
            valor_total=0.0,  # TODO: Buscar da venda
            valor_icms=0.0,
            valor_ipi=0.0,
            status=StatusNotaEnum.PENDENTE,
            observacoes=emissao_data.observacoes,
        )

        nota = await self.repository.create(nota_data)

        # Simula autorização imediata (em produção, aguardaria retorno da SEFAZ)
        nota = await self.repository.registrar_autorizacao(
            nota.id, protocolo="SIMULADO-123456", data_autorizacao=datetime.now()
        )

        await self.session.flush()
        await self.session.refresh(nota)

        return NotaFiscalResponse.model_validate(nota)

    def _gerar_chave_simulada(self) -> str:
        """
        Gera uma chave de acesso simulada de 44 dígitos

        Returns:
            Chave de acesso simulada
        """
        # Em produção, usaria algoritmo oficial de geração de chave
        timestamp = str(int(datetime.now().timestamp()))
        chave = timestamp.ljust(44, "0")
        return chave[:44]

    async def consultar_nota(self, nota_id: int) -> ConsultarNotaResponse:
        """
        Consulta nota por ID com XML completo

        Args:
            nota_id: ID da nota

        Returns:
            ConsultarNotaResponse com dados completos

        Raises:
            NotFoundException: Se nota não encontrada
        """
        nota = await self.repository.get_by_id(nota_id)
        if not nota:
            raise NotFoundException(f"Nota fiscal {nota_id} não encontrada")

        return ConsultarNotaResponse.model_validate(nota)

    async def consultar_por_chave(self, chave_acesso: str) -> ConsultarNotaResponse:
        """
        Consulta nota por chave de acesso

        Args:
            chave_acesso: Chave de acesso da nota

        Returns:
            ConsultarNotaResponse com dados completos

        Raises:
            NotFoundException: Se nota não encontrada
            ValidationException: Se chave inválida
        """
        # Valida formato da chave
        chave_limpa = chave_acesso.strip().replace(" ", "")
        if len(chave_limpa) != 44 or not chave_limpa.isdigit():
            raise ValidationException("Chave de acesso inválida (deve ter 44 dígitos)")

        nota = await self.repository.get_by_chave(chave_limpa)
        if not nota:
            raise NotFoundException(
                f"Nota fiscal com chave {chave_limpa} não encontrada"
            )

        return ConsultarNotaResponse.model_validate(nota)

    async def cancelar_nota(self, nota_id: int, motivo: str) -> NotaFiscalResponse:
        """
        Cancela uma nota fiscal

        Args:
            nota_id: ID da nota
            motivo: Motivo do cancelamento

        Returns:
            NotaFiscalResponse com nota cancelada

        Raises:
            NotFoundException: Se nota não encontrada
            BusinessRuleException: Se nota não pode ser cancelada
        """
        nota = await self.repository.get_by_id(nota_id)
        if not nota:
            raise NotFoundException(f"Nota fiscal {nota_id} não encontrada")

        # Valida se pode cancelar
        if nota.status == StatusNota.CANCELADA:
            raise BusinessRuleException("Nota já está cancelada")

        if nota.status == StatusNota.REJEITADA:
            raise BusinessRuleException("Nota rejeitada não pode ser cancelada")

        # Em produção, enviaria cancelamento para SEFAZ
        observacao = f"CANCELAMENTO: {motivo}"
        nota = await self.repository.atualizar_status(
            nota_id, StatusNota.CANCELADA, observacao
        )

        await self.session.flush()
        await self.session.refresh(nota)

        return NotaFiscalResponse.model_validate(nota)

    async def get_notas_periodo(
        self,
        data_inicio: datetime,
        data_fim: datetime,
        page: int = 1,
        page_size: int = 50,
        tipo: Optional[TipoNotaEnum] = None,
        status: Optional[StatusNotaEnum] = None,
    ) -> NotaFiscalList:
        """
        Lista notas por período

        Args:
            data_inicio: Data inicial
            data_fim: Data final
            page: Página atual
            page_size: Tamanho da página
            tipo: Filtrar por tipo
            status: Filtrar por status

        Returns:
            NotaFiscalList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte enums para tipos do modelo
        tipo_db = TipoNota(tipo.value) if tipo else None
        status_db = StatusNota(status.value) if status else None

        # Busca notas e total
        notas = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            tipo=tipo_db,
            status=status_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.repository.count(
            tipo=tipo_db,
            status=status_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return NotaFiscalList(
            items=[NotaFiscalResponse.model_validate(n) for n in notas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def listar_notas(
        self,
        page: int = 1,
        page_size: int = 50,
        tipo: Optional[TipoNotaEnum] = None,
        status: Optional[StatusNotaEnum] = None,
        fornecedor_id: Optional[int] = None,
        venda_id: Optional[int] = None,
    ) -> NotaFiscalList:
        """
        Lista notas com paginação e filtros

        Args:
            page: Página atual
            page_size: Tamanho da página
            tipo: Filtrar por tipo
            status: Filtrar por status
            fornecedor_id: Filtrar por fornecedor
            venda_id: Filtrar por venda

        Returns:
            NotaFiscalList com lista paginada
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte enums para tipos do modelo
        tipo_db = TipoNota(tipo.value) if tipo else None
        status_db = StatusNota(status.value) if status else None

        # Busca notas e total
        notas = await self.repository.get_all(
            skip=skip,
            limit=page_size,
            tipo=tipo_db,
            status=status_db,
            fornecedor_id=fornecedor_id,
            venda_id=venda_id,
        )

        total = await self.repository.count(
            tipo=tipo_db,
            status=status_db,
            fornecedor_id=fornecedor_id,
            venda_id=venda_id,
        )

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return NotaFiscalList(
            items=[NotaFiscalResponse.model_validate(n) for n in notas],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
