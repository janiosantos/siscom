"""
Serviço para geração e processamento de arquivos CNAB 240/400
CNAB = Centro Nacional de Automação Bancária
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pagamentos.models import (
    ConfiguracaoBoleto,
    Boleto,
    ExtratoBancario,
    StatusBoleto
)

logger = logging.getLogger(__name__)


class CNABService:
    """Serviço para operações com arquivos CNAB"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========== CNAB 240 (Layout moderno) ==========

    async def gerar_cnab240_remessa(
        self,
        configuracao_id: int,
        boletos: List[Boleto],
        numero_remessa: int = 1
    ) -> str:
        """
        Gera arquivo CNAB 240 de remessa (envio de boletos ao banco)

        Args:
            configuracao_id: ID da configuração bancária
            boletos: Lista de boletos a serem enviados
            numero_remessa: Número sequencial do arquivo de remessa

        Returns:
            Conteúdo do arquivo CNAB 240
        """
        logger.info(
            f"Gerando CNAB 240 remessa - Config: {configuracao_id}, "
            f"Boletos: {len(boletos)}, Nº Remessa: {numero_remessa}"
        )

        # Buscar configuração
        stmt = select(ConfiguracaoBoleto).where(ConfiguracaoBoleto.id == configuracao_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            raise ValueError(f"Configuração {configuracao_id} não encontrada")

        linhas = []

        # Header do Arquivo (Registro 0)
        linhas.append(self._gerar_header_arquivo_240(config, numero_remessa))

        # Header do Lote (Registro 1)
        linhas.append(self._gerar_header_lote_240(config, 1))

        # Detalhe - Segmento P e Q para cada boleto
        sequencial = 1
        for boleto in boletos:
            # Segmento P - Dados do boleto
            linhas.append(self._gerar_segmento_p_240(config, boleto, 1, sequencial))
            sequencial += 1

            # Segmento Q - Dados do sacado
            linhas.append(self._gerar_segmento_q_240(config, boleto, 1, sequencial))
            sequencial += 1

            # Segmento R - Opcional (multa, juros, descontos)
            linhas.append(self._gerar_segmento_r_240(config, boleto, 1, sequencial))
            sequencial += 1

        # Trailer do Lote (Registro 5)
        linhas.append(self._gerar_trailer_lote_240(len(boletos), 1))

        # Trailer do Arquivo (Registro 9)
        linhas.append(self._gerar_trailer_arquivo_240(1))

        conteudo = "\r\n".join(linhas)

        logger.info(f"CNAB 240 remessa gerado com sucesso - {len(linhas)} registros")
        return conteudo

    async def processar_cnab240_retorno(
        self,
        configuracao_id: int,
        conteudo_arquivo: str
    ) -> Dict[str, Any]:
        """
        Processa arquivo CNAB 240 de retorno (resposta do banco)

        Args:
            configuracao_id: ID da configuração bancária
            conteudo_arquivo: Conteúdo do arquivo CNAB 240

        Returns:
            Dicionário com estatísticas do processamento
        """
        logger.info(f"Processando CNAB 240 retorno - Config: {configuracao_id}")

        linhas = conteudo_arquivo.strip().split("\n")
        total_registros = 0
        boletos_atualizados = 0
        boletos_pagos = 0
        erros = []

        for idx, linha in enumerate(linhas):
            linha = linha.strip()
            if not linha or len(linha) != 240:
                continue

            tipo_registro = linha[7:8]

            # Processar apenas Segmento T (retorno de cobrança)
            if tipo_registro == "3" and linha[13:14] == "T":
                try:
                    resultado = await self._processar_segmento_t_240(linha)
                    total_registros += 1

                    if resultado["atualizado"]:
                        boletos_atualizados += 1

                    if resultado["pago"]:
                        boletos_pagos += 1

                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 1}: {str(e)}")
                    erros.append({"linha": idx + 1, "erro": str(e)})

        await self.db.commit()

        logger.info(
            f"CNAB 240 retorno processado - Atualizados: {boletos_atualizados}, "
            f"Pagos: {boletos_pagos}, Erros: {len(erros)}"
        )

        return {
            "total_registros": total_registros,
            "boletos_atualizados": boletos_atualizados,
            "boletos_pagos": boletos_pagos,
            "erros": erros
        }

    # ========== CNAB 400 (Layout antigo) ==========

    async def gerar_cnab400_remessa(
        self,
        configuracao_id: int,
        boletos: List[Boleto],
        numero_remessa: int = 1
    ) -> str:
        """
        Gera arquivo CNAB 400 de remessa (formato legado)

        Args:
            configuracao_id: ID da configuração bancária
            boletos: Lista de boletos
            numero_remessa: Número sequencial do arquivo

        Returns:
            Conteúdo do arquivo CNAB 400
        """
        logger.info(
            f"Gerando CNAB 400 remessa - Config: {configuracao_id}, "
            f"Boletos: {len(boletos)}"
        )

        stmt = select(ConfiguracaoBoleto).where(ConfiguracaoBoleto.id == configuracao_id)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            raise ValueError(f"Configuração {configuracao_id} não encontrada")

        linhas = []

        # Header do Arquivo (Registro 0)
        linhas.append(self._gerar_header_arquivo_400(config, numero_remessa))

        # Detalhe para cada boleto (Registro 1)
        for idx, boleto in enumerate(boletos, start=1):
            linhas.append(self._gerar_detalhe_400(config, boleto, idx))

        # Trailer do Arquivo (Registro 9)
        linhas.append(self._gerar_trailer_arquivo_400(len(boletos)))

        conteudo = "\r\n".join(linhas)

        logger.info(f"CNAB 400 remessa gerado com sucesso - {len(linhas)} registros")
        return conteudo

    async def processar_cnab400_retorno(
        self,
        configuracao_id: int,
        conteudo_arquivo: str
    ) -> Dict[str, Any]:
        """
        Processa arquivo CNAB 400 de retorno

        Args:
            configuracao_id: ID da configuração bancária
            conteudo_arquivo: Conteúdo do arquivo CNAB 400

        Returns:
            Dicionário com estatísticas
        """
        logger.info(f"Processando CNAB 400 retorno - Config: {configuracao_id}")

        linhas = conteudo_arquivo.strip().split("\n")
        total_registros = 0
        boletos_atualizados = 0
        boletos_pagos = 0
        erros = []

        for idx, linha in enumerate(linhas):
            linha = linha.strip()
            if not linha or len(linha) != 400:
                continue

            tipo_registro = linha[0:1]

            # Processar apenas Registro 1 (Detalhe)
            if tipo_registro == "1":
                try:
                    resultado = await self._processar_detalhe_400(linha)
                    total_registros += 1

                    if resultado["atualizado"]:
                        boletos_atualizados += 1

                    if resultado["pago"]:
                        boletos_pagos += 1

                except Exception as e:
                    logger.error(f"Erro ao processar linha {idx + 1}: {str(e)}")
                    erros.append({"linha": idx + 1, "erro": str(e)})

        await self.db.commit()

        logger.info(
            f"CNAB 400 retorno processado - Atualizados: {boletos_atualizados}, "
            f"Pagos: {boletos_pagos}"
        )

        return {
            "total_registros": total_registros,
            "boletos_atualizados": boletos_atualizados,
            "boletos_pagos": boletos_pagos,
            "erros": erros
        }

    # ========== Métodos auxiliares CNAB 240 ==========

    def _gerar_header_arquivo_240(
        self, config: ConfiguracaoBoleto, numero_remessa: int
    ) -> str:
        """Gera header do arquivo CNAB 240 (Registro 0)"""
        linha = ""
        linha += config.banco_codigo.zfill(3)  # Código do banco
        linha += "0000"  # Lote de serviço
        linha += "0"  # Tipo de registro
        linha += " " * 9  # Uso exclusivo FEBRABAN
        linha += "2"  # Tipo de inscrição (2 = CNPJ)
        linha += config.cedente_cnpj.zfill(14)  # CNPJ
        linha += " " * 20  # Convênio
        linha += config.agencia.zfill(5)  # Agência
        linha += (config.agencia_dv or " ").ljust(1)  # DV agência
        linha += config.conta.zfill(12)  # Conta
        linha += (config.conta_dv or " ").ljust(1)  # DV conta
        linha += " "  # DV agência/conta
        linha += config.cedente_nome[:30].ljust(30)  # Nome da empresa
        linha += config.banco_nome[:30].ljust(30)  # Nome do banco
        linha += " " * 10  # Uso exclusivo FEBRABAN
        linha += "1"  # Código de remessa
        linha += datetime.now().strftime("%d%m%Y")  # Data de geração
        linha += datetime.now().strftime("%H%M%S")  # Hora de geração
        linha += str(numero_remessa).zfill(6)  # Número sequencial do arquivo
        linha += "103"  # Versão do layout
        linha += "00000"  # Densidade de gravação
        linha += " " * 20  # Uso reservado banco
        linha += " " * 20  # Uso reservado empresa
        linha += " " * 29  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_header_lote_240(self, config: ConfiguracaoBoleto, lote: int) -> str:
        """Gera header do lote CNAB 240 (Registro 1)"""
        linha = ""
        linha += config.banco_codigo.zfill(3)
        linha += str(lote).zfill(4)
        linha += "1"  # Tipo de registro
        linha += "R"  # Tipo de operação (R = Remessa)
        linha += "01"  # Tipo de serviço (01 = Cobrança)
        linha += "  "  # Uso exclusivo FEBRABAN
        linha += "060"  # Versão do layout do lote
        linha += " "  # Uso exclusivo FEBRABAN
        linha += "2"  # Tipo de inscrição
        linha += config.cedente_cnpj.zfill(15)
        linha += " " * 20  # Convênio
        linha += config.agencia.zfill(5)
        linha += (config.agencia_dv or " ").ljust(1)
        linha += config.conta.zfill(12)
        linha += (config.conta_dv or " ").ljust(1)
        linha += " "  # DV agência/conta
        linha += config.cedente_nome[:30].ljust(30)
        linha += " " * 80  # Mensagem
        linha += " " * 8  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_segmento_p_240(
        self, config: ConfiguracaoBoleto, boleto: Boleto, lote: int, sequencial: int
    ) -> str:
        """Gera Segmento P CNAB 240 (dados do boleto)"""
        linha = ""
        linha += config.banco_codigo.zfill(3)
        linha += str(lote).zfill(4)
        linha += "3"  # Tipo de registro
        linha += str(sequencial).zfill(5)
        linha += "P"  # Código do segmento
        linha += " "  # Uso exclusivo FEBRABAN
        linha += "01"  # Código de movimento (01 = Entrada de títulos)
        linha += config.agencia.zfill(5)
        linha += (config.agencia_dv or " ").ljust(1)
        linha += config.conta.zfill(12)
        linha += (config.conta_dv or " ").ljust(1)
        linha += " "  # DV agência/conta
        linha += boleto.nosso_numero[:20].ljust(20)
        linha += config.carteira.zfill(1)
        linha += "1"  # Forma de cadastramento (1 = Com cadastramento)
        linha += "1"  # Tipo de documento (1 = Tradicional)
        linha += "2"  # Identificação da emissão (2 = Cliente emite)
        linha += "2"  # Identificação da distribuição (2 = Cliente distribui)
        linha += boleto.numero_documento[:15].ljust(15)
        linha += boleto.data_vencimento.strftime("%d%m%Y")
        linha += str(int(boleto.valor * 100)).zfill(15)  # Valor em centavos
        linha += "00000"  # Agência cobradora
        linha += " "  # DV agência cobradora
        linha += "01"  # Espécie do título (01 = Duplicata Mercantil)
        linha += "N"  # Aceite (N = Não aceite)
        linha += boleto.data_emissao.strftime("%d%m%Y")
        linha += "1"  # Código de juros (1 = Valor por dia)
        linha += "00000000"  # Data de juros
        linha += str(int((boleto.valor * config.juros_mes / 100 / 30) * 100)).zfill(15)
        linha += "0"  # Código de desconto (0 = Sem desconto)
        linha += "00000000"  # Data de desconto
        linha += "000000000000000"  # Valor de desconto
        linha += "000000000000000"  # Valor IOF
        linha += "000000000000000"  # Valor abatimento
        linha += " " * 25  # Uso da empresa
        linha += "0"  # Código de protesto (0 = Não protestar)
        linha += str(config.dias_protesto or 0).zfill(2)
        linha += "0"  # Código de baixa (0 = Não baixar)
        linha += "000"  # Prazo de baixa
        linha += "09"  # Código da moeda (09 = Real)
        linha += "0000000000"  # Uso exclusivo FEBRABAN
        linha += " "  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_segmento_q_240(
        self, config: ConfiguracaoBoleto, boleto: Boleto, lote: int, sequencial: int
    ) -> str:
        """Gera Segmento Q CNAB 240 (dados do sacado)"""
        linha = ""
        linha += config.banco_codigo.zfill(3)
        linha += str(lote).zfill(4)
        linha += "3"  # Tipo de registro
        linha += str(sequencial).zfill(5)
        linha += "Q"  # Código do segmento
        linha += " "  # Uso exclusivo FEBRABAN
        linha += "01"  # Código de movimento
        linha += "1" if len(boleto.sacado_cpf_cnpj) == 11 else "2"  # Tipo inscrição (1=CPF, 2=CNPJ)
        linha += boleto.sacado_cpf_cnpj.zfill(15)
        linha += boleto.sacado_nome[:40].ljust(40)
        linha += (boleto.sacado_endereco or "")[:40].ljust(40)
        linha += (boleto.sacado_bairro or "")[:15].ljust(15)
        linha += (boleto.sacado_cep or "").replace("-", "").zfill(8)
        linha += (boleto.sacado_cidade or "")[:15].ljust(15)
        linha += (boleto.sacado_uf or "").ljust(2)
        linha += "0"  # Tipo de inscrição do avalista (0 = Sem avalista)
        linha += "000000000000000"  # Inscrição do avalista
        linha += " " * 40  # Nome do avalista
        linha += " " * 3  # Uso exclusivo FEBRABAN
        linha += " " * 20  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_segmento_r_240(
        self, config: ConfiguracaoBoleto, boleto: Boleto, lote: int, sequencial: int
    ) -> str:
        """Gera Segmento R CNAB 240 (multa, juros, descontos)"""
        linha = ""
        linha += config.banco_codigo.zfill(3)
        linha += str(lote).zfill(4)
        linha += "3"  # Tipo de registro
        linha += str(sequencial).zfill(5)
        linha += "R"  # Código do segmento
        linha += " "  # Uso exclusivo FEBRABAN
        linha += "01"  # Código de movimento
        linha += "0"  # Código de desconto 2
        linha += "00000000"  # Data de desconto 2
        linha += "000000000000000"  # Valor/percentual desconto 2
        linha += "0"  # Código de desconto 3
        linha += "00000000"  # Data de desconto 3
        linha += "000000000000000"  # Valor/percentual desconto 3
        linha += "2"  # Código de multa (2 = Percentual)
        linha += (boleto.data_vencimento + timedelta(days=1)).strftime("%d%m%Y")
        linha += str(int(config.multa_atraso * 100)).zfill(15)  # Percentual em centavos
        linha += " " * 10  # Informação ao sacado
        linha += " " * 40  # Mensagem 3
        linha += " " * 40  # Mensagem 4
        linha += " " * 61  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_trailer_lote_240(self, qtd_boletos: int, lote: int) -> str:
        """Gera trailer do lote CNAB 240 (Registro 5)"""
        qtd_registros = (qtd_boletos * 3) + 2  # P + Q + R por boleto + header + trailer
        linha = ""
        linha += "000"  # Código do banco (será preenchido)
        linha += str(lote).zfill(4)
        linha += "5"  # Tipo de registro
        linha += " " * 9  # Uso exclusivo FEBRABAN
        linha += str(qtd_registros).zfill(6)
        linha += " " * 217  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    def _gerar_trailer_arquivo_240(self, qtd_lotes: int) -> str:
        """Gera trailer do arquivo CNAB 240 (Registro 9)"""
        linha = ""
        linha += "000"  # Código do banco
        linha += "9999"  # Lote de serviço
        linha += "9"  # Tipo de registro
        linha += " " * 9  # Uso exclusivo FEBRABAN
        linha += str(qtd_lotes).zfill(6)
        linha += " " * 6  # Qtd registros (será calculado)
        linha += " " * 205  # Uso exclusivo FEBRABAN
        return linha.ljust(240)

    async def _processar_segmento_t_240(self, linha: str) -> Dict[str, Any]:
        """Processa Segmento T do retorno CNAB 240"""
        nosso_numero = linha[37:57].strip()
        codigo_ocorrencia = linha[15:17]
        valor_pago = Decimal(linha[77:92]) / 100
        data_pagamento_str = linha[137:145]

        # Buscar boleto
        stmt = select(Boleto).where(Boleto.nosso_numero == nosso_numero)
        result = await self.db.execute(stmt)
        boleto = result.scalar_one_or_none()

        if not boleto:
            logger.warning(f"Boleto não encontrado - Nosso número: {nosso_numero}")
            return {"atualizado": False, "pago": False}

        # Processar ocorrência
        pago = False
        if codigo_ocorrencia == "06":  # Liquidação
            boleto.status = StatusBoleto.PAGO
            boleto.valor_pago = valor_pago
            boleto.data_pagamento = datetime.strptime(data_pagamento_str, "%d%m%Y").date()
            pago = True
            logger.info(f"Boleto {nosso_numero} marcado como PAGO - Valor: {valor_pago}")

        return {"atualizado": True, "pago": pago}

    # ========== Métodos auxiliares CNAB 400 ==========

    def _gerar_header_arquivo_400(
        self, config: ConfiguracaoBoleto, numero_remessa: int
    ) -> str:
        """Gera header do arquivo CNAB 400 (Registro 0)"""
        linha = ""
        linha += "0"  # Tipo de registro
        linha += "1"  # Tipo de operação (1 = Remessa)
        linha += "REMESSA".ljust(7)
        linha += "01"  # Código de serviço
        linha += "COBRANCA".ljust(15)
        linha += config.agencia.zfill(4)
        linha += (config.agencia_dv or "0").ljust(2)
        linha += config.conta.zfill(8)
        linha += (config.conta_dv or "0").ljust(1)
        linha += " " * 6  # Uso da empresa
        linha += config.cedente_nome[:30].ljust(30)
        linha += config.banco_codigo.zfill(3)
        linha += config.banco_nome[:15].ljust(15)
        linha += datetime.now().strftime("%d%m%y")
        linha += " " * 294  # Brancos
        linha += str(numero_remessa).zfill(6)
        return linha.ljust(400)

    def _gerar_detalhe_400(
        self, config: ConfiguracaoBoleto, boleto: Boleto, sequencial: int
    ) -> str:
        """Gera registro de detalhe CNAB 400 (Registro 1)"""
        linha = ""
        linha += "1"  # Tipo de registro
        linha += "2"  # Tipo de inscrição (2 = CNPJ)
        linha += config.cedente_cnpj.zfill(14)
        linha += config.agencia.zfill(4)
        linha += (config.agencia_dv or "0").ljust(2)
        linha += config.conta.zfill(8)
        linha += (config.conta_dv or "0").ljust(1)
        linha += " " * 25  # Uso da empresa
        linha += boleto.nosso_numero.zfill(11)
        linha += "01"  # Carteira
        linha += "  "  # Identificação da ocorrência
        linha += boleto.numero_documento[:10].ljust(10)
        linha += boleto.data_vencimento.strftime("%d%m%y")
        linha += str(int(boleto.valor * 100)).zfill(13)
        linha += "000"  # Código do banco
        linha += "00000"  # Agência cobradora
        linha += "01"  # Espécie do título
        linha += "N"  # Aceite
        linha += boleto.data_emissao.strftime("%d%m%y")
        linha += "00"  # Instrução 1
        linha += "00"  # Instrução 2
        linha += str(int((boleto.valor * config.juros_mes / 100 / 30) * 100)).zfill(13)
        linha += " " * 6  # Data de desconto
        linha += "0000000000000"  # Valor de desconto
        linha += "0000000000000"  # Valor IOF
        linha += "0000000000000"  # Abatimento
        linha += "1" if len(boleto.sacado_cpf_cnpj) == 11 else "2"
        linha += boleto.sacado_cpf_cnpj.zfill(14)
        linha += boleto.sacado_nome[:40].ljust(40)
        linha += (boleto.sacado_endereco or "")[:40].ljust(40)
        linha += " " * 12  # Mensagem
        linha += (boleto.sacado_cep or "").replace("-", "").zfill(8)
        linha += " " * 60  # Uso do banco
        linha += str(sequencial).zfill(6)
        return linha.ljust(400)

    def _gerar_trailer_arquivo_400(self, qtd_boletos: int) -> str:
        """Gera trailer do arquivo CNAB 400 (Registro 9)"""
        linha = ""
        linha += "9"  # Tipo de registro
        linha += " " * 393  # Brancos
        linha += str(qtd_boletos + 2).zfill(6)  # Total de registros (+ header + trailer)
        return linha.ljust(400)

    async def _processar_detalhe_400(self, linha: str) -> Dict[str, Any]:
        """Processa registro de detalhe do retorno CNAB 400"""
        nosso_numero = linha[62:73].strip()
        codigo_ocorrencia = linha[108:110]
        valor_pago = Decimal(linha[253:266]) / 100 if linha[253:266].strip() else Decimal("0")
        data_pagamento_str = linha[110:116]

        # Buscar boleto
        stmt = select(Boleto).where(Boleto.nosso_numero.contains(nosso_numero))
        result = await self.db.execute(stmt)
        boleto = result.scalar_one_or_none()

        if not boleto:
            logger.warning(f"Boleto não encontrado - Nosso número: {nosso_numero}")
            return {"atualizado": False, "pago": False}

        # Processar ocorrência
        pago = False
        if codigo_ocorrencia == "06":  # Liquidação
            boleto.status = StatusBoleto.PAGO
            boleto.valor_pago = valor_pago
            if data_pagamento_str.strip():
                boleto.data_pagamento = datetime.strptime(data_pagamento_str, "%d%m%y").date()
            pago = True
            logger.info(f"Boleto {nosso_numero} marcado como PAGO - Valor: {valor_pago}")

        return {"atualizado": True, "pago": pago}


# Importação adicional necessária
from datetime import timedelta
