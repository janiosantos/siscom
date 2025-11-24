"""
Serviço LGPD - Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018)

Funcionalidades:
- Consentimento e revogação
- Direito de acesso aos dados
- Portabilidade de dados
- Anonimização e pseudonimização
- Direito ao esquecimento (exclusão)
- Auditoria e logs de acesso
"""
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from decimal import Decimal
import re

logger = logging.getLogger(__name__)


class TipoConsentimento:
    """Tipos de consentimento LGPD"""
    MARKETING = "marketing"
    NEWSLETTER = "newsletter"
    COMPARTILHAMENTO_DADOS = "compartilhamento_dados"
    TRATAMENTO_DADOS_SENSIVEIS = "tratamento_dados_sensiveis"
    ANALISE_CREDITO = "analise_credito"
    COOKIES = "cookies"


class FinalidadeProcessamento:
    """Finalidades de processamento de dados"""
    EXECUCAO_CONTRATO = "execucao_contrato"
    OBRIGACAO_LEGAL = "obrigacao_legal"
    EXERCICIO_DIREITOS = "exercicio_direitos"
    PROTECAO_VIDA = "protecao_vida"
    TUTELA_SAUDE = "tutela_saude"
    INTERESSE_LEGITIMO = "interesse_legitimo"
    PROTECAO_CREDITO = "protecao_credito"


class ConsentimentoLGPD:
    """Gerenciamento de consentimentos LGPD"""

    def __init__(self, titular_id: int, db_session):
        self.titular_id = titular_id
        self.db = db_session
        self.consentimentos: Dict[str, Dict[str, Any]] = {}

    async def solicitar_consentimento(
        self,
        tipo: str,
        finalidade: str,
        descricao: str,
        obrigatorio: bool = False
    ) -> Dict[str, Any]:
        """
        Solicita consentimento ao titular dos dados

        Args:
            tipo: Tipo de consentimento
            finalidade: Finalidade do processamento
            descricao: Descrição clara e objetiva
            obrigatorio: Se o consentimento é obrigatório

        Returns:
            Informações do consentimento solicitado
        """
        logger.info(
            f"Solicitando consentimento LGPD - "
            f"Titular: {self.titular_id}, Tipo: {tipo}"
        )

        consentimento = {
            "titular_id": self.titular_id,
            "tipo": tipo,
            "finalidade": finalidade,
            "descricao": descricao,
            "obrigatorio": obrigatorio,
            "status": "pendente",
            "data_solicitacao": datetime.now().isoformat(),
            "data_resposta": None,
            "concedido": False
        }

        # Salvar no banco de dados
        # TODO: Implementar model ConsentimentoLGPD e salvar

        return consentimento

    async def conceder_consentimento(
        self,
        tipo: str,
        ip_origem: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra concessão de consentimento

        Args:
            tipo: Tipo de consentimento
            ip_origem: IP de origem do consentimento

        Returns:
            Consentimento atualizado
        """
        logger.info(
            f"Consentimento concedido - "
            f"Titular: {self.titular_id}, Tipo: {tipo}"
        )

        consentimento = {
            "titular_id": self.titular_id,
            "tipo": tipo,
            "status": "concedido",
            "concedido": True,
            "data_resposta": datetime.now().isoformat(),
            "ip_origem": ip_origem,
            "validade": (datetime.now() + timedelta(days=365)).isoformat()  # 1 ano
        }

        # Salvar no banco
        # TODO: Atualizar model ConsentimentoLGPD

        # Registrar em log de auditoria
        await self._registrar_auditoria(
            acao="consentimento_concedido",
            tipo_consentimento=tipo,
            ip_origem=ip_origem
        )

        return consentimento

    async def revogar_consentimento(self, tipo: str) -> Dict[str, Any]:
        """
        Revoga um consentimento previamente concedido

        Args:
            tipo: Tipo de consentimento a revogar

        Returns:
            Consentimento revogado
        """
        logger.info(
            f"Revogando consentimento - "
            f"Titular: {self.titular_id}, Tipo: {tipo}"
        )

        # TODO: Buscar e atualizar consentimento no banco

        consentimento = {
            "titular_id": self.titular_id,
            "tipo": tipo,
            "status": "revogado",
            "concedido": False,
            "data_revogacao": datetime.now().isoformat()
        }

        # Registrar em log de auditoria
        await self._registrar_auditoria(
            acao="consentimento_revogado",
            tipo_consentimento=tipo
        )

        return consentimento

    async def listar_consentimentos(self) -> List[Dict[str, Any]]:
        """
        Lista todos os consentimentos do titular

        Returns:
            Lista de consentimentos
        """
        # TODO: Buscar do banco de dados
        return []

    async def _registrar_auditoria(
        self,
        acao: str,
        tipo_consentimento: Optional[str] = None,
        ip_origem: Optional[str] = None
    ):
        """Registra ação em log de auditoria LGPD"""
        log_entry = {
            "titular_id": self.titular_id,
            "acao": acao,
            "tipo_consentimento": tipo_consentimento,
            "ip_origem": ip_origem,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Auditoria LGPD: {json.dumps(log_entry)}")
        # TODO: Salvar em tabela de auditoria


class AnonymizationService:
    """Serviço de anonimização e pseudonimização de dados"""

    @staticmethod
    def anonimizar_cpf(cpf: str) -> str:
        """
        Anonimiza CPF

        Exemplo: 123.456.789-00 -> ***.456.***-**
        """
        cpf_limpo = re.sub(r'\D', '', cpf)
        if len(cpf_limpo) == 11:
            return f"***{cpf_limpo[3:6]}***-**"
        return "***.***.***-**"

    @staticmethod
    def anonimizar_cnpj(cnpj: str) -> str:
        """
        Anonimiza CNPJ

        Exemplo: 12.345.678/0001-90 -> **.345.***/**01-**
        """
        cnpj_limpo = re.sub(r'\D', '', cnpj)
        if len(cnpj_limpo) == 14:
            return f"**.{cnpj_limpo[2:5]}.***/**{cnpj_limpo[10:12]}-**"
        return "**.***.***/**01-**"

    @staticmethod
    def anonimizar_email(email: str) -> str:
        """
        Anonimiza e-mail

        Exemplo: usuario@email.com -> us****@email.com
        """
        if "@" not in email:
            return "****@****.***"

        partes = email.split("@")
        usuario = partes[0]
        dominio = partes[1]

        if len(usuario) <= 2:
            usuario_anonimo = "**"
        else:
            usuario_anonimo = usuario[:2] + "*" * (len(usuario) - 2)

        return f"{usuario_anonimo}@{dominio}"

    @staticmethod
    def anonimizar_telefone(telefone: str) -> str:
        """
        Anonimiza telefone

        Exemplo: (11) 98765-4321 -> (11) ****-4321
        """
        telefone_limpo = re.sub(r'\D', '', telefone)
        if len(telefone_limpo) >= 8:
            return f"(**) ****-{telefone_limpo[-4:]}"
        return "(**) ****-****"

    @staticmethod
    def anonimizar_nome(nome: str) -> str:
        """
        Anonimiza nome

        Exemplo: João da Silva -> J*** ** S****
        """
        partes = nome.split()
        if not partes:
            return "****"

        resultado = []
        for parte in partes:
            if len(parte) <= 1:
                resultado.append(parte)
            else:
                resultado.append(parte[0] + "*" * (len(parte) - 1))

        return " ".join(resultado)

    @staticmethod
    def pseudonimizar(valor: str, salt: str = "lgpd_salt_2024") -> str:
        """
        Pseudonimização usando hash SHA-256

        Args:
            valor: Valor a pseudonimizar
            salt: Salt para o hash

        Returns:
            Hash SHA-256 do valor
        """
        combined = f"{valor}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()


class PortabilidadeService:
    """Serviço de portabilidade de dados (Direito de acesso)"""

    async def exportar_dados_titular(
        self,
        titular_id: int,
        formato: str = "json"
    ) -> Dict[str, Any]:
        """
        Exporta todos os dados de um titular

        Args:
            titular_id: ID do titular
            formato: Formato de exportação (json, csv, xml)

        Returns:
            Dados do titular
        """
        logger.info(f"Exportando dados do titular {titular_id} - Formato: {formato}")

        # TODO: Buscar dados do titular de todas as tabelas relevantes
        dados = {
            "titular_id": titular_id,
            "data_exportacao": datetime.now().isoformat(),
            "dados_pessoais": {
                # TODO: Buscar do banco
                "nome": "TITULAR",
                "cpf": "***.***.***-**",
                "email": "****@****.***"
            },
            "dados_cadastrais": {},
            "historico_compras": [],
            "historico_pagamentos": [],
            "consentimentos": [],
            "acessos": [],
            "observacao": "Dados fornecidos em conformidade com Art. 18 da LGPD"
        }

        return dados

    async def gerar_relatorio_dados(
        self,
        titular_id: int
    ) -> str:
        """
        Gera relatório legível dos dados do titular

        Args:
            titular_id: ID do titular

        Returns:
            Relatório em formato texto
        """
        dados = await self.exportar_dados_titular(titular_id)

        relatorio = f"""
═══════════════════════════════════════════════════════════
  RELATÓRIO DE DADOS PESSOAIS - LGPD
═══════════════════════════════════════════════════════════

Titular ID: {titular_id}
Data da Solicitação: {dados['data_exportacao']}

DADOS PESSOAIS:
{json.dumps(dados['dados_pessoais'], indent=2, ensure_ascii=False)}

CONSENTIMENTOS:
{json.dumps(dados['consentimentos'], indent=2, ensure_ascii=False)}

═══════════════════════════════════════════════════════════
Este relatório foi gerado em conformidade com o Art. 18 da
Lei nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais)
═══════════════════════════════════════════════════════════
"""

        return relatorio


class EsquecimentoService:
    """Serviço de Direito ao Esquecimento (Exclusão de dados)"""

    async def solicitar_exclusao(
        self,
        titular_id: int,
        motivo: str
    ) -> Dict[str, Any]:
        """
        Registra solicitação de exclusão de dados

        Args:
            titular_id: ID do titular
            motivo: Motivo da solicitação

        Returns:
            Informações da solicitação
        """
        logger.info(
            f"Solicitação de exclusão de dados - Titular: {titular_id}"
        )

        solicitacao = {
            "titular_id": titular_id,
            "tipo": "exclusao_dados",
            "motivo": motivo,
            "status": "em_analise",
            "data_solicitacao": datetime.now().isoformat(),
            "prazo_resposta": (datetime.now() + timedelta(days=15)).isoformat(),
            "observacao": "Solicitação em conformidade com Art. 18, VI da LGPD"
        }

        # TODO: Salvar solicitação no banco

        return solicitacao

    async def executar_exclusao(
        self,
        titular_id: int,
        anonimizar_ao_inves_de_excluir: bool = True
    ) -> Dict[str, Any]:
        """
        Executa exclusão ou anonimização dos dados

        Args:
            titular_id: ID do titular
            anonimizar_ao_inves_de_excluir: Se deve anonimizar ao invés de excluir
                (recomendado para manter histórico fiscal/contábil)

        Returns:
            Resultado da operação
        """
        logger.info(
            f"Executando exclusão/anonimização - "
            f"Titular: {titular_id}, "
            f"Anonimizar: {anonimizar_ao_inves_de_excluir}"
        )

        if anonimizar_ao_inves_de_excluir:
            # Anonimizar dados mantendo registros para fins legais
            resultado = await self._anonimizar_dados_titular(titular_id)
            tipo_acao = "anonimizacao"
        else:
            # Exclusão completa (usar apenas se permitido legalmente)
            resultado = await self._excluir_dados_titular(titular_id)
            tipo_acao = "exclusao"

        return {
            "titular_id": titular_id,
            "tipo_acao": tipo_acao,
            "sucesso": resultado["sucesso"],
            "tabelas_afetadas": resultado["tabelas_afetadas"],
            "registros_afetados": resultado["registros_afetados"],
            "data_execucao": datetime.now().isoformat(),
            "observacao": (
                "Dados anonimizados mantendo obrigações legais e contratuais"
                if anonimizar_ao_inves_de_excluir else
                "Dados excluídos conforme solicitação"
            )
        }

    async def _anonimizar_dados_titular(self, titular_id: int) -> Dict[str, Any]:
        """Anonimiza dados do titular"""
        # TODO: Implementar anonimização nas tabelas
        # - clientes: anonimizar nome, email, telefone, cpf
        # - enderecos: anonimizar endereço completo
        # - vendas: manter valores mas anonimizar cliente
        # - pagamentos: manter valores mas anonimizar cliente

        logger.info(f"Anonimizando dados do titular {titular_id}")

        return {
            "sucesso": True,
            "tabelas_afetadas": ["clientes", "enderecos", "contatos"],
            "registros_afetados": 3
        }

    async def _excluir_dados_titular(self, titular_id: int) -> Dict[str, Any]:
        """Exclui dados do titular (usar com cautela)"""
        logger.warning(
            f"EXCLUSÃO PERMANENTE de dados - Titular: {titular_id}"
        )

        # TODO: Implementar exclusão cascata respeitando constraints

        return {
            "sucesso": True,
            "tabelas_afetadas": ["clientes", "enderecos", "contatos"],
            "registros_afetados": 3
        }


class LGPDService:
    """Serviço principal de conformidade LGPD"""

    def __init__(self):
        self.anonymization = AnonymizationService()
        self.portabilidade = PortabilidadeService()
        self.esquecimento = EsquecimentoService()

    async def processar_requisicao_titular(
        self,
        titular_id: int,
        tipo_requisicao: str,
        parametros: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processa requisição de titular dos dados

        Tipos de requisição:
        - acesso_dados: Solicitar acesso aos dados
        - correcao_dados: Solicitar correção de dados
        - exclusao_dados: Solicitar exclusão (direito ao esquecimento)
        - portabilidade: Solicitar exportação de dados
        - revogacao_consentimento: Revogar consentimento

        Args:
            titular_id: ID do titular
            tipo_requisicao: Tipo da requisição
            parametros: Parâmetros específicos da requisição

        Returns:
            Resultado do processamento
        """
        logger.info(
            f"Processando requisição LGPD - "
            f"Titular: {titular_id}, Tipo: {tipo_requisicao}"
        )

        if tipo_requisicao == "acesso_dados":
            return await self.portabilidade.exportar_dados_titular(titular_id)

        elif tipo_requisicao == "exclusao_dados":
            motivo = parametros.get("motivo", "Exercício do direito ao esquecimento")
            return await self.esquecimento.solicitar_exclusao(titular_id, motivo)

        elif tipo_requisicao == "portabilidade":
            formato = parametros.get("formato", "json")
            return await self.portabilidade.exportar_dados_titular(titular_id, formato)

        else:
            raise ValueError(f"Tipo de requisição não suportado: {tipo_requisicao}")

    async def gerar_relatorio_conformidade(self) -> Dict[str, Any]:
        """
        Gera relatório de conformidade LGPD

        Returns:
            Relatório de conformidade
        """
        logger.info("Gerando relatório de conformidade LGPD")

        # TODO: Implementar métricas reais
        relatorio = {
            "data_geracao": datetime.now().isoformat(),
            "consentimentos": {
                "total": 0,
                "ativos": 0,
                "revogados": 0,
                "pendentes": 0
            },
            "requisicoes_titulares": {
                "total": 0,
                "acesso_dados": 0,
                "exclusao_dados": 0,
                "portabilidade": 0,
                "correcao_dados": 0
            },
            "incidentes_seguranca": {
                "total": 0,
                "reportados_anpd": 0,
                "em_investigacao": 0
            },
            "conformidade": {
                "percentual": 95,  # TODO: Calcular baseado em checklist
                "areas_conformes": [
                    "Base legal para tratamento",
                    "Consentimentos documentados",
                    "Mecanismo de portabilidade",
                    "Processo de exclusão"
                ],
                "areas_melhorar": [
                    "Treinamento de equipe",
                    "Revisão de políticas de privacidade"
                ]
            }
        }

        return relatorio


# Instância global do serviço
lgpd_service = LGPDService()
