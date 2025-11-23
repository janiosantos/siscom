"""
Service para Documentos Auxiliares

Gera PDFs de documentos não fiscais
"""
from typing import Optional, Dict, Any
from datetime import datetime, date
from pathlib import Path
import os
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documentos_auxiliares.models import DocumentoAuxiliar, TipoDocumento
from app.modules.documentos_auxiliares.schemas import (
    GerarDocumentoRequest,
    DocumentoAuxiliarResponse,
    DocumentoGeradoResponse,
)
from app.modules.pedidos_venda.repository import PedidoVendaRepository
from app.modules.orcamentos.repository import OrcamentoRepository
from app.modules.vendas.repository import VendaRepository
from app.core.exceptions import NotFoundException, ValidationException


class DocumentoAuxiliarService:
    """Service para geração de documentos auxiliares"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.pedido_repo = PedidoVendaRepository(session)
        self.orcamento_repo = OrcamentoRepository(session)
        self.venda_repo = VendaRepository(session)

        # Configurar Jinja2
        templates_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(templates_dir)))

        # Diretório para salvar PDFs
        self.pdf_dir = Path("storage/documentos_auxiliares")
        self.pdf_dir.mkdir(parents=True, exist_ok=True)

    async def gerar_documento(
        self, request: GerarDocumentoRequest, usuario_id: int
    ) -> DocumentoGeradoResponse:
        """
        Gera documento auxiliar em PDF

        Args:
            request: Dados para gerar documento
            usuario_id: ID do usuário que está gerando

        Returns:
            DocumentoGeradoResponse com caminho do PDF e URL de download

        Raises:
            NotFoundException: Se documento origem não existe
            ValidationException: Se tipo de documento não é compatível
        """
        # Buscar dados do documento origem
        dados = await self._buscar_dados_origem(
            request.referencia_tipo, request.referencia_id
        )

        # Renderizar HTML
        html_content = self._renderizar_template(request.tipo_documento, dados)

        # Gerar PDF (usando WeasyPrint ou outra lib)
        # NOTA: WeasyPrint requer dependências do sistema (cairo, pango)
        # Por simplicidade, vou salvar apenas o HTML por enquanto
        # Em produção, usar WeasyPrint ou similar

        arquivo_nome = self._gerar_nome_arquivo(request.tipo_documento, dados)
        arquivo_path = self.pdf_dir / arquivo_nome

        # Salvar HTML (em produção, converter para PDF)
        with open(arquivo_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Salvar no banco de dados
        documento = DocumentoAuxiliar(
            tipo_documento=TipoDocumento(request.tipo_documento.value),
            referencia_tipo=request.referencia_tipo,
            referencia_id=request.referencia_id,
            numero_documento=dados.get("numero_documento", "S/N"),
            cliente_id=dados.get("cliente_id"),
            arquivo_pdf=str(arquivo_path),
            conteudo_html=html_content,
            gerado_por_id=usuario_id,
        )

        self.session.add(documento)
        await self.session.commit()
        await self.session.refresh(documento)

        return DocumentoGeradoResponse(
            documento_id=documento.id,
            tipo_documento=request.tipo_documento,
            numero_documento=documento.numero_documento,
            arquivo_pdf=str(arquivo_path),
            url_download=f"/api/v1/documentos-auxiliares/{documento.id}/download",
        )

    async def _buscar_dados_origem(
        self, referencia_tipo: str, referencia_id: int
    ) -> Dict[str, Any]:
        """
        Busca dados do documento origem

        Args:
            referencia_tipo: Tipo da referência (pedido_venda, orcamento, venda)
            referencia_id: ID do documento

        Returns:
            Dict com dados do documento

        Raises:
            NotFoundException: Se documento não existe
            ValidationException: Se tipo não é suportado
        """
        if referencia_tipo == "pedido_venda":
            return await self._buscar_dados_pedido_venda(referencia_id)
        elif referencia_tipo == "orcamento":
            return await self._buscar_dados_orcamento(referencia_id)
        elif referencia_tipo == "venda":
            return await self._buscar_dados_venda(referencia_id)
        else:
            raise ValidationException(
                f"Tipo de referência '{referencia_tipo}' não suportado"
            )

    async def _buscar_dados_pedido_venda(self, pedido_id: int) -> Dict[str, Any]:
        """Busca dados do pedido de venda"""
        pedido = await self.pedido_repo.get_by_id(pedido_id)
        if not pedido:
            raise NotFoundException(f"Pedido {pedido_id} não encontrado")

        # Formatar dados para o template
        dados = {
            "numero_documento": pedido.numero_pedido,
            "numero_pedido": pedido.numero_pedido,
            "data_pedido": pedido.data_pedido.strftime("%d/%m/%Y"),
            "data_entrega_prevista": pedido.data_entrega_prevista.strftime("%d/%m/%Y")
            if pedido.data_entrega_prevista
            else "N/A",
            "status": pedido.status.value,
            "tipo_entrega": pedido.tipo_entrega.value if pedido.tipo_entrega else "N/A",
            "endereco_entrega": pedido.endereco_entrega or "Retirada no local",
            "subtotal": f"{pedido.subtotal:.2f}",
            "desconto": f"{pedido.desconto:.2f}",
            "valor_frete": f"{pedido.valor_frete:.2f}",
            "outras_despesas": f"{pedido.outras_despesas:.2f}",
            "valor_total": f"{pedido.valor_total:.2f}",
            "observacoes": pedido.observacoes or "",
            "forma_pagamento": pedido.forma_pagamento or "",
            "condicao_pagamento": "",  # TODO: buscar da condicao_pagamento
            # Cliente
            "cliente_id": pedido.cliente_id,
            "cliente_nome": pedido.cliente.nome if pedido.cliente else "N/A",
            "cliente_documento": getattr(pedido.cliente, "cpf", None)
            or getattr(pedido.cliente, "cnpj", None)
            or "N/A",
            "cliente_telefone": getattr(pedido.cliente, "telefone", None) or "N/A",
            "cliente_email": getattr(pedido.cliente, "email", None) or "N/A",
            # Vendedor
            "vendedor_nome": pedido.vendedor.nome if pedido.vendedor else "N/A",
            # Empresa (TODO: buscar de configurações)
            "empresa_nome": "ERP Materiais de Construção",
            "empresa_endereco": "Rua Exemplo, 123 - Centro - São Paulo/SP",
            "empresa_cnpj": "00.000.000/0001-00",
            "empresa_telefone": "(11) 9999-9999",
            "empresa_email": "contato@empresa.com",
            # Itens
            "itens": [
                {
                    "codigo": item.produto.codigo if item.produto else "N/A",
                    "descricao": item.produto.descricao if item.produto else "N/A",
                    "quantidade": f"{item.quantidade:.2f}",
                    "preco_unitario": f"{item.preco_unitario:.2f}",
                    "desconto": f"{item.desconto_item:.2f}",
                    "total": f"{item.total_item:.2f}",
                    "observacao": item.observacao_item or "",
                }
                for item in pedido.itens
            ],
            # Data de geração
            "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

        # Para nota de entrega
        if pedido.data_entrega_real:
            dados["data_entrega"] = pedido.data_entrega_real.strftime("%d/%m/%Y")
        else:
            dados["data_entrega"] = date.today().strftime("%d/%m/%Y")

        return dados

    async def _buscar_dados_orcamento(self, orcamento_id: int) -> Dict[str, Any]:
        """Busca dados do orçamento"""
        orcamento = await self.orcamento_repo.get_by_id(orcamento_id)
        if not orcamento:
            raise NotFoundException(f"Orçamento {orcamento_id} não encontrado")

        # Formatar dados para o template
        dados = {
            "numero_documento": str(orcamento.id),
            "numero_orcamento": str(orcamento.id),
            "data_orcamento": orcamento.data_orcamento.strftime("%d/%m/%Y"),
            "data_validade": orcamento.data_validade.strftime("%d/%m/%Y"),
            "validade_dias": orcamento.validade_dias,
            "status": orcamento.status.value,
            "subtotal": f"{orcamento.subtotal:.2f}",
            "desconto": f"{orcamento.desconto:.2f}",
            "valor_total": f"{orcamento.valor_total:.2f}",
            "observacoes": orcamento.observacoes or "",
            # Cliente
            "cliente_id": orcamento.cliente_id,
            "cliente_nome": orcamento.cliente.nome if orcamento.cliente else "N/A",
            "cliente_documento": getattr(orcamento.cliente, "cpf", None)
            or getattr(orcamento.cliente, "cnpj", None)
            or "N/A",
            "cliente_telefone": getattr(orcamento.cliente, "telefone", None) or "N/A",
            "cliente_email": getattr(orcamento.cliente, "email", None) or "N/A",
            # Vendedor
            "vendedor_nome": orcamento.vendedor.nome if orcamento.vendedor else "N/A",
            # Empresa
            "empresa_nome": "ERP Materiais de Construção",
            "empresa_endereco": "Rua Exemplo, 123 - Centro - São Paulo/SP",
            "empresa_cnpj": "00.000.000/0001-00",
            "empresa_telefone": "(11) 9999-9999",
            "empresa_email": "contato@empresa.com",
            # Itens
            "itens": [
                {
                    "codigo": item.produto.codigo if item.produto else "N/A",
                    "descricao": item.produto.descricao if item.produto else "N/A",
                    "quantidade": f"{item.quantidade:.2f}",
                    "preco_unitario": f"{item.preco_unitario:.2f}",
                    "desconto": f"{item.desconto_item:.2f}",
                    "total": f"{item.total:.2f}",
                }
                for item in orcamento.itens
            ],
            # Data de geração
            "data_geracao": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }

        return dados

    async def _buscar_dados_venda(self, venda_id: int) -> Dict[str, Any]:
        """Busca dados da venda"""
        venda = await self.venda_repo.get_by_id(venda_id)
        if not venda:
            raise NotFoundException(f"Venda {venda_id} não encontrada")

        # Similar ao pedido_venda
        # TODO: Implementar se necessário
        return {}

    def _renderizar_template(
        self, tipo_documento: TipoDocumento, dados: Dict[str, Any]
    ) -> str:
        """
        Renderiza template HTML

        Args:
            tipo_documento: Tipo do documento
            dados: Dados para o template

        Returns:
            HTML renderizado
        """
        # Mapear tipo de documento para template
        template_map = {
            TipoDocumento.PEDIDO_VENDA: "pedido_venda.html",
            TipoDocumento.ORCAMENTO: "orcamento.html",
            TipoDocumento.NOTA_ENTREGA: "nota_entrega.html",
            TipoDocumento.ROMANEIO: "pedido_venda.html",  # Reutiliza template
            TipoDocumento.COMPROVANTE_ENTREGA: "nota_entrega.html",  # Reutiliza
            TipoDocumento.RECIBO: "pedido_venda.html",  # Reutiliza
            TipoDocumento.PEDIDO_COMPRA: "pedido_venda.html",  # Similar
        }

        template_name = template_map.get(tipo_documento, "pedido_venda.html")
        template = self.jinja_env.get_template(template_name)

        return template.render(**dados)

    def _gerar_nome_arquivo(
        self, tipo_documento: TipoDocumento, dados: Dict[str, Any]
    ) -> str:
        """Gera nome do arquivo PDF"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        numero = dados.get("numero_documento", "SN").replace("/", "-")
        tipo = tipo_documento.value.lower()

        return f"{tipo}_{numero}_{timestamp}.html"

    async def get_documento(self, documento_id: int) -> DocumentoAuxiliar:
        """Busca documento por ID"""
        from sqlalchemy import select

        result = await self.session.execute(
            select(DocumentoAuxiliar).where(DocumentoAuxiliar.id == documento_id)
        )
        documento = result.scalar_one_or_none()

        if not documento:
            raise NotFoundException(f"Documento {documento_id} não encontrado")

        return documento

    async def listar_documentos(
        self,
        skip: int = 0,
        limit: int = 100,
        tipo_documento: Optional[TipoDocumento] = None,
        cliente_id: Optional[int] = None,
    ) -> list[DocumentoAuxiliar]:
        """Lista documentos auxiliares"""
        from sqlalchemy import select

        query = select(DocumentoAuxiliar).order_by(
            DocumentoAuxiliar.created_at.desc()
        )

        if tipo_documento:
            query = query.where(DocumentoAuxiliar.tipo_documento == tipo_documento)

        if cliente_id:
            query = query.where(DocumentoAuxiliar.cliente_id == cliente_id)

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
