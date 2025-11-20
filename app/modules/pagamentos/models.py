"""
Models para Pagamentos (PIX, Boleto, Conciliação)
"""
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Numeric, Date, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class TipoPagamento(str, enum.Enum):
    """Tipos de pagamento"""
    PIX = "pix"
    BOLETO = "boleto"
    CARTAO_CREDITO = "cartao_credito"
    CARTAO_DEBITO = "cartao_debito"
    DINHEIRO = "dinheiro"
    TRANSFERENCIA = "transferencia"
    CHEQUE = "cheque"


class StatusPagamento(str, enum.Enum):
    """Status de pagamento"""
    PENDENTE = "pendente"
    PROCESSANDO = "processando"
    APROVADO = "aprovado"
    REJEITADO = "rejeitado"
    CANCELADO = "cancelado"
    ESTORNADO = "estornado"
    EXPIRADO = "expirado"


class TipoChavePix(str, enum.Enum):
    """Tipos de chave PIX"""
    CPF = "cpf"
    CNPJ = "cnpj"
    EMAIL = "email"
    TELEFONE = "telefone"
    ALEATORIA = "aleatoria"


class StatusBoleto(str, enum.Enum):
    """Status de boleto"""
    ABERTO = "aberto"
    REGISTRADO = "registrado"
    PAGO = "pago"
    VENCIDO = "vencido"
    CANCELADO = "cancelado"
    BAIXADO = "baixado"


# ==============================================================================
# Models PIX
# ==============================================================================

class ChavePix(Base):
    """
    Modelo de Chave PIX

    Armazena chaves PIX da empresa para recebimento
    """
    __tablename__ = 'chaves_pix'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tipo: Mapped[TipoChavePix] = mapped_column(SQLEnum(TipoChavePix), nullable=False)
    chave: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    descricao: Mapped[str] = mapped_column(String(255), nullable=True)
    banco: Mapped[str] = mapped_column(String(100), nullable=False)
    agencia: Mapped[str] = mapped_column(String(10), nullable=False)
    conta: Mapped[str] = mapped_column(String(20), nullable=False)
    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    transacoes_pix: Mapped[list["TransacaoPix"]] = relationship("TransacaoPix", back_populates="chave_pix")

    def __repr__(self):
        return f"<ChavePix(tipo={self.tipo}, chave={self.chave})>"


class TransacaoPix(Base):
    """
    Modelo de Transação PIX

    Registra transações PIX (enviadas e recebidas)
    """
    __tablename__ = 'transacoes_pix'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    txid: Mapped[str] = mapped_column(String(35), unique=True, index=True, nullable=False)  # Transaction ID BACEN
    e2e_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=True)  # End-to-End ID

    # Dados da transação
    chave_pix_id: Mapped[int] = mapped_column(ForeignKey('chaves_pix.id'), nullable=False, index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    descricao: Mapped[str] = mapped_column(Text, nullable=True)

    # Pagador
    pagador_nome: Mapped[str] = mapped_column(String(255), nullable=True)
    pagador_documento: Mapped[str] = mapped_column(String(14), nullable=True)  # CPF/CNPJ

    # Status e datas
    status: Mapped[StatusPagamento] = mapped_column(SQLEnum(StatusPagamento), default=StatusPagamento.PENDENTE)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    data_pagamento: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    data_expiracao: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # QR Code (para cobrança)
    qr_code_texto: Mapped[str] = mapped_column(Text, nullable=True)  # Texto do QR Code (copia e cola)
    qr_code_imagem: Mapped[str] = mapped_column(Text, nullable=True)  # Base64 da imagem QR Code

    # Webhook e metadados
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=True)
    extra_metadata: Mapped[str] = mapped_column(Text, nullable=True)  # JSON com dados adicionais

    # Integração com gateways externos (Mercado Pago, PagSeguro, etc)
    integration_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)  # ID no sistema externo
    integration_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # mercadopago, pagseguro, etc
    integration_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON com dados do provider

    # Relacionamentos
    chave_pix: Mapped["ChavePix"] = relationship("ChavePix", back_populates="transacoes_pix")

    def __repr__(self):
        return f"<TransacaoPix(txid={self.txid}, valor={self.valor}, status={self.status})>"


# ==============================================================================
# Models Boleto
# ==============================================================================

class ConfiguracaoBoleto(Base):
    """
    Configuração de Boleto Bancário

    Armazena configurações por banco para geração de boletos
    """
    __tablename__ = 'configuracoes_boleto'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    banco_codigo: Mapped[str] = mapped_column(String(3), nullable=False)  # 001, 033, 104, 237, etc
    banco_nome: Mapped[str] = mapped_column(String(100), nullable=False)
    agencia: Mapped[str] = mapped_column(String(10), nullable=False)
    agencia_dv: Mapped[str] = mapped_column(String(1), nullable=True)
    conta: Mapped[str] = mapped_column(String(20), nullable=False)
    conta_dv: Mapped[str] = mapped_column(String(2), nullable=False)

    # Cedente (empresa que emite o boleto)
    cedente_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    cedente_documento: Mapped[str] = mapped_column(String(14), nullable=False)
    cedente_endereco: Mapped[str] = mapped_column(String(500), nullable=True)

    # Configurações do boleto
    carteira: Mapped[str] = mapped_column(String(3), nullable=False)  # Ex: 175 (Itaú)
    convenio: Mapped[str] = mapped_column(String(20), nullable=True)  # Convênio/Código do cedente
    variacao_carteira: Mapped[str] = mapped_column(String(3), nullable=True)

    # Instruções padrão
    instrucoes: Mapped[str] = mapped_column(Text, nullable=True)
    local_pagamento: Mapped[str] = mapped_column(String(255), default="Pagável em qualquer banco até o vencimento")

    # Juros e multa
    percentual_juros: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)  # % ao mês
    percentual_multa: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, nullable=False)  # %

    ativa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    boletos: Mapped[list["Boleto"]] = relationship("Boleto", back_populates="configuracao")

    def __repr__(self):
        return f"<ConfiguracaoBoleto(banco={self.banco_codigo}, agencia={self.agencia}, conta={self.conta})>"


class Boleto(Base):
    """
    Modelo de Boleto Bancário
    """
    __tablename__ = 'boletos'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    configuracao_id: Mapped[int] = mapped_column(ForeignKey('configuracoes_boleto.id'), nullable=False)

    # Dados do boleto
    nosso_numero: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    numero_documento: Mapped[str] = mapped_column(String(20), nullable=False)
    codigo_barras: Mapped[str] = mapped_column(String(44), nullable=True)
    linha_digitavel: Mapped[str] = mapped_column(String(54), nullable=True)

    # Valores
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valor_desconto: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    valor_pago: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)
    valor_juros: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    valor_multa: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=0, nullable=False)

    # Datas
    data_emissao: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    data_vencimento: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=True)
    data_baixa: Mapped[date] = mapped_column(Date, nullable=True)

    # Sacado (pagador)
    sacado_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    sacado_documento: Mapped[str] = mapped_column(String(14), nullable=False)
    sacado_endereco: Mapped[str] = mapped_column(String(500), nullable=True)
    sacado_cep: Mapped[str] = mapped_column(String(8), nullable=True)
    sacado_cidade: Mapped[str] = mapped_column(String(100), nullable=True)
    sacado_uf: Mapped[str] = mapped_column(String(2), nullable=True)

    # Instruções
    instrucoes: Mapped[str] = mapped_column(Text, nullable=True)
    demonstrativo: Mapped[str] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[StatusBoleto] = mapped_column(SQLEnum(StatusBoleto), default=StatusBoleto.REGISTRADO)

    # Registro no banco
    registrado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_registro: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # PDF
    pdf_path: Mapped[str] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacionamentos
    configuracao: Mapped["ConfiguracaoBoleto"] = relationship("ConfiguracaoBoleto", back_populates="boletos")

    def __repr__(self):
        return f"<Boleto(nosso_numero={self.nosso_numero}, valor={self.valor}, status={self.status})>"


# ==============================================================================
# Models Conciliação Bancária
# ==============================================================================

class ExtratoBancario(Base):
    """
    Extrato Bancário importado

    Armazena lançamentos do extrato bancário para conciliação
    """
    __tablename__ = 'extratos_bancarios'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    banco_codigo: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    agencia: Mapped[str] = mapped_column(String(10), nullable=False)
    conta: Mapped[str] = mapped_column(String(20), nullable=False)

    # Dados do lançamento
    data: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(500), nullable=False)
    documento: Mapped[str] = mapped_column(String(50), nullable=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tipo: Mapped[str] = mapped_column(String(1), nullable=False)  # C=Crédito, D=Débito
    saldo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=True)

    # Conciliação
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    data_conciliacao: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    conciliacao_id: Mapped[int] = mapped_column(ForeignKey('conciliacoes_bancarias.id'), nullable=True)

    # Import
    arquivo_origem: Mapped[str] = mapped_column(String(500), nullable=True)
    linha_arquivo: Mapped[int] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    conciliacao: Mapped[Optional["ConciliacaoBancaria"]] = relationship(
        "ConciliacaoBancaria",
        back_populates="lancamentos"
    )

    def __repr__(self):
        return f"<ExtratoBancario(data={self.data}, valor={self.valor}, conciliado={self.conciliado})>"


class ConciliacaoBancaria(Base):
    """
    Conciliação Bancária

    Relaciona lançamentos do extrato com transações do sistema
    """
    __tablename__ = 'conciliacoes_bancarias'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Tipo de conciliação
    tipo: Mapped[str] = mapped_column(String(50), nullable=False)  # pix, boleto, transferencia, etc

    # IDs relacionados
    transacao_pix_id: Mapped[int] = mapped_column(ForeignKey('transacoes_pix.id'), nullable=True)
    boleto_id: Mapped[int] = mapped_column(ForeignKey('boletos.id'), nullable=True)

    # Dados da conciliação
    valor_sistema: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valor_extrato: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    diferenca: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # Automática ou manual
    automatica: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usuario_id: Mapped[int] = mapped_column(nullable=True)  # Usuário que fez conciliação manual

    # Observações
    observacoes: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    lancamentos: Mapped[list["ExtratoBancario"]] = relationship(
        "ExtratoBancario",
        back_populates="conciliacao"
    )

    def __repr__(self):
        return f"<ConciliacaoBancaria(tipo={self.tipo}, diferenca={self.diferenca})>"
