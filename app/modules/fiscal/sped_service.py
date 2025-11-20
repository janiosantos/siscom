"""
Serviço para geração de arquivos SPED Fiscal (EFD-ICMS/IPI)
Sistema Público de Escrituração Digital
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from io import StringIO

logger = logging.getLogger(__name__)


class SPEDFiscal:
    """Gerador de arquivo SPED Fiscal"""

    def __init__(
        self,
        empresa: Dict[str, Any],
        periodo_inicial: date,
        periodo_final: date,
        finalidade: str = "0"  # 0=Original, 1=Substituto
    ):
        self.empresa = empresa
        self.periodo_inicial = periodo_inicial
        self.periodo_final = periodo_final
        self.finalidade = finalidade
        self.registros: List[str] = []

    def adicionar_registro_0000(self):
        """
        Registro 0000: Abertura do Arquivo Digital e Identificação da Entidade
        """
        reg = "|0000|"
        reg += "014|"  # Código da versão do leiaute (014 = versão 3.0.8)
        reg += "0|"  # Código da finalidade (0 = Original)
        reg += self.periodo_inicial.strftime("%d%m%Y") + "|"
        reg += self.periodo_final.strftime("%d%m%Y") + "|"
        reg += self.empresa["razao_social"] + "|"
        reg += self.empresa["cnpj"].replace(".", "").replace("/", "").replace("-", "") + "|"
        reg += self.empresa["ie"] + "|"  # Inscrição Estadual
        reg += self.empresa.get("im", "") + "|"  # Inscrição Municipal
        reg += self.empresa.get("uf", "SP") + "|"
        reg += "1|"  # Código do Indicador da atividade (1 = Industrial)

        self.registros.append(reg)

    def adicionar_registro_0001(self):
        """
        Registro 0001: Abertura do Bloco 0
        """
        reg = "|0001|"
        reg += "0|"  # Indicador de movimento (0 = Bloco com dados)

        self.registros.append(reg)

    def adicionar_registro_0005(self, estabelecimento: Dict[str, Any]):
        """
        Registro 0005: Dados Complementares da Entidade
        """
        reg = "|0005|"
        reg += estabelecimento.get("fantasia", self.empresa["razao_social"]) + "|"
        reg += (estabelecimento.get("cep", "")).replace("-", "") + "|"
        reg += estabelecimento.get("endereco", "") + "|"
        reg += estabelecimento.get("numero", "SN") + "|"
        reg += estabelecimento.get("complemento", "") + "|"
        reg += estabelecimento.get("bairro", "") + "|"
        reg += estabelecimento.get("telefone", "") + "|"
        reg += estabelecimento.get("fax", "") + "|"
        reg += estabelecimento.get("email", "") + "|"

        self.registros.append(reg)

    def adicionar_registro_0015(self, participante: Dict[str, Any]):
        """
        Registro 0015: Dados dos Participantes (Clientes/Fornecedores)
        """
        reg = "|0015|"

        # CNPJ ou CPF
        doc = participante["cnpj_cpf"].replace(".", "").replace("/", "").replace("-", "")
        if len(doc) == 11:
            reg += "2|"  # Tipo (2 = CPF)
            reg += "|"  # CNPJ vazio
            reg += doc + "|"  # CPF
        else:
            reg += "1|"  # Tipo (1 = CNPJ)
            reg += doc + "|"  # CNPJ
            reg += "|"  # CPF vazio

        reg += participante["nome"] + "|"
        reg += participante.get("codigo", str(participante.get("id", ""))) + "|"
        reg += participante.get("endereco", "") + "|"
        reg += participante.get("numero", "SN") + "|"
        reg += participante.get("complemento", "") + "|"
        reg += participante.get("bairro", "") + "|"

        self.registros.append(reg)

    def adicionar_registro_0200(self, produto: Dict[str, Any]):
        """
        Registro 0200: Tabela de Identificação do Item (Produto/Serviço)
        """
        reg = "|0200|"
        reg += str(produto["codigo"]) + "|"
        reg += produto["descricao"] + "|"
        reg += "|"  # Descrição complementar
        reg += "00|"  # Tipo do item (00 = Mercadoria para revenda)
        reg += str(produto.get("ncm", "00000000")) + "|"
        reg += produto.get("codigo_barras", "") + "|"
        reg += produto.get("unidade", "UN") + "|"

        self.registros.append(reg)

    def adicionar_registro_C100(self, nota_fiscal: Dict[str, Any]):
        """
        Registro C100: Documento - Nota Fiscal (código 01), Nota Fiscal Avulsa (código 1B),
        Nota Fiscal de Produtor (código 04), NF-e (código 55) e NFC-e (código 65)
        """
        reg = "|C100|"
        reg += "0|"  # Indicador do tipo de operação (0 = Entrada, 1 = Saída)
        reg += "1|"  # Indicador do emitente (0 = Próprio, 1 = Terceiros)
        reg += str(nota_fiscal["participante_id"]) + "|"  # Código do participante
        reg += nota_fiscal["modelo"] + "|"  # Modelo (55 = NF-e, 65 = NFC-e)
        reg += "|"  # Código da situação do documento
        reg += str(nota_fiscal["serie"]) + "|"
        reg += str(nota_fiscal["numero"]) + "|"
        reg += nota_fiscal.get("chave_acesso", "") + "|"
        reg += nota_fiscal["data_emissao"].strftime("%d%m%Y") + "|"
        reg += nota_fiscal.get("data_entrada_saida", nota_fiscal["data_emissao"]).strftime("%d%m%Y") + "|"
        reg += f"{nota_fiscal['valor_total']:.2f}".replace(".", ",") + "|"
        reg += "0|"  # Indicador do tipo de pagamento (0 = à vista, 1 = a prazo, 9 = sem pagamento)
        reg += f"{nota_fiscal.get('valor_desconto', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_abatimento', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_mercadorias', nota_fiscal['valor_total']):.2f}".replace(".", ",") + "|"
        reg += "0|"  # Indicador do tipo de frete (0 = por conta do emitente, 1 = por conta do destinatário, etc)
        reg += f"{nota_fiscal.get('valor_frete', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_seguro', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('outras_despesas', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_icms', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_icms_st', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_ipi', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_pis', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_cofins', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_pis_st', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{nota_fiscal.get('valor_cofins_st', Decimal('0.00')):.2f}".replace(".", ",") + "|"

        self.registros.append(reg)

    def adicionar_registro_C170(self, item_nf: Dict[str, Any]):
        """
        Registro C170: Complemento de Documento - Itens do Documento
        """
        reg = "|C170|"
        reg += str(item_nf["numero_item"]) + "|"
        reg += str(item_nf["produto_id"]) + "|"
        reg += item_nf["descricao"] + "|"
        reg += f"{item_nf['quantidade']:.4f}".replace(".", ",") + "|"
        reg += item_nf.get("unidade", "UN") + "|"
        reg += f"{item_nf['valor_total']:.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('desconto', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += "0|"  # Indicador de movimentação física
        reg += item_nf.get("cst_icms", "000") + "|"  # CST ICMS
        reg += item_nf.get("cfop", "5102") + "|"  # CFOP
        reg += "|"  # Código da conta analítica contábil
        reg += f"{item_nf.get('valor_icms', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('base_icms', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('aliquota_icms', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('valor_ipi', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('base_ipi', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += f"{item_nf.get('aliquota_ipi', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += item_nf.get("cst_pis", "99") + "|"  # CST PIS
        reg += f"{item_nf.get('valor_pis', Decimal('0.00')):.2f}".replace(".", ",") + "|"
        reg += item_nf.get("cst_cofins", "99") + "|"  # CST COFINS
        reg += f"{item_nf.get('valor_cofins', Decimal('0.00')):.2f}".replace(".", ",") + "|"

        self.registros.append(reg)

    def adicionar_registro_9999(self):
        """
        Registro 9999: Encerramento do Arquivo Digital
        """
        total_linhas = len(self.registros) + 1  # +1 para incluir este próprio registro

        reg = "|9999|"
        reg += str(total_linhas) + "|"

        self.registros.append(reg)

    def gerar_arquivo(self) -> str:
        """
        Gera o conteúdo completo do arquivo SPED Fiscal

        Returns:
            Conteúdo do arquivo SPED
        """
        logger.info(
            f"Gerando SPED Fiscal - Período: "
            f"{self.periodo_inicial} a {self.periodo_final}"
        )

        # Limpar registros anteriores
        self.registros = []

        # Adicionar registros obrigatórios
        self.adicionar_registro_0000()
        self.adicionar_registro_0001()

        # Registro de encerramento será adicionado no final
        # após adicionar todos os outros registros

        return "\n".join(self.registros)

    def exportar(self) -> str:
        """
        Exporta o arquivo SPED completo

        Returns:
            String com o conteúdo do arquivo
        """
        # Adicionar registro de encerramento
        self.adicionar_registro_9999()

        conteudo = self.gerar_arquivo()

        logger.info(f"SPED Fiscal gerado - Total de registros: {len(self.registros)}")

        return conteudo


class SPEDService:
    """Serviço para gerenciamento de SPED Fiscal"""

    def gerar_sped_fiscal(
        self,
        empresa: Dict[str, Any],
        periodo_inicial: date,
        periodo_final: date,
        notas_fiscais: List[Dict[str, Any]],
        participantes: List[Dict[str, Any]],
        produtos: List[Dict[str, Any]]
    ) -> str:
        """
        Gera arquivo SPED Fiscal completo

        Args:
            empresa: Dados da empresa
            periodo_inicial: Data inicial do período
            periodo_final: Data final do período
            notas_fiscais: Lista de notas fiscais do período
            participantes: Lista de clientes/fornecedores
            produtos: Lista de produtos

        Returns:
            Conteúdo do arquivo SPED
        """
        logger.info(
            f"Iniciando geração de SPED Fiscal - Empresa: {empresa['razao_social']}"
        )

        sped = SPEDFiscal(
            empresa=empresa,
            periodo_inicial=periodo_inicial,
            periodo_final=periodo_final
        )

        # Bloco 0: Abertura, Identificação e Referências
        sped.adicionar_registro_0000()
        sped.adicionar_registro_0001()

        # Estabelecimento
        sped.adicionar_registro_0005(empresa)

        # Participantes
        for participante in participantes:
            sped.adicionar_registro_0015(participante)

        # Produtos
        for produto in produtos:
            sped.adicionar_registro_0200(produto)

        # Bloco C: Documentos Fiscais I
        for nf in notas_fiscais:
            sped.adicionar_registro_C100(nf)

            # Itens da NF
            for item in nf.get("itens", []):
                sped.adicionar_registro_C170(item)

        # Registro de encerramento
        sped.adicionar_registro_9999()

        conteudo = sped.gerar_arquivo()

        logger.info(
            f"SPED Fiscal gerado com sucesso - "
            f"{len(notas_fiscais)} NFs, "
            f"{len(self.registros)} registros"
        )

        return conteudo

    def validar_sped(self, conteudo: str) -> Dict[str, Any]:
        """
        Valida estrutura básica do arquivo SPED

        Args:
            conteudo: Conteúdo do arquivo SPED

        Returns:
            Resultado da validação
        """
        logger.info("Validando arquivo SPED Fiscal")

        linhas = conteudo.strip().split("\n")
        erros = []
        avisos = []

        # Verificar primeiro registro (0000)
        if not linhas[0].startswith("|0000|"):
            erros.append("Arquivo deve iniciar com registro 0000")

        # Verificar último registro (9999)
        if not linhas[-1].startswith("|9999|"):
            erros.append("Arquivo deve terminar com registro 9999")

        # Verificar total de linhas declarado
        try:
            total_declarado = int(linhas[-1].split("|")[2])
            total_real = len(linhas)

            if total_declarado != total_real:
                erros.append(
                    f"Total de linhas divergente: "
                    f"declarado {total_declarado}, encontrado {total_real}"
                )
        except (IndexError, ValueError) as e:
            erros.append(f"Erro ao validar total de linhas: {str(e)}")

        # Verificar estrutura dos registros
        for idx, linha in enumerate(linhas):
            if not linha.startswith("|") or not linha.endswith("|"):
                erros.append(f"Linha {idx + 1}: Formato inválido")

        resultado = {
            "valido": len(erros) == 0,
            "total_linhas": len(linhas),
            "erros": erros,
            "avisos": avisos
        }

        if resultado["valido"]:
            logger.info("Arquivo SPED válido")
        else:
            logger.warning(f"Arquivo SPED inválido - {len(erros)} erros")

        return resultado

    def gerar_relatorio_apuracao_icms(
        self,
        notas_fiscais: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Gera relatório de apuração de ICMS

        Args:
            notas_fiscais: Lista de notas fiscais

        Returns:
            Relatório de apuração
        """
        logger.info("Gerando relatório de apuração de ICMS")

        # Calcular totais
        icms_entradas = Decimal("0.00")
        icms_saidas = Decimal("0.00")
        base_icms_entradas = Decimal("0.00")
        base_icms_saidas = Decimal("0.00")

        for nf in notas_fiscais:
            valor_icms = nf.get("valor_icms", Decimal("0.00"))
            base_icms = nf.get("base_icms", Decimal("0.00"))

            if nf.get("tipo") == "entrada":
                icms_entradas += valor_icms
                base_icms_entradas += base_icms
            else:
                icms_saidas += valor_icms
                base_icms_saidas += base_icms

        # Apuração
        saldo_credor = max(Decimal("0.00"), icms_saidas - icms_entradas)
        saldo_devedor = max(Decimal("0.00"), icms_entradas - icms_saidas)

        relatorio = {
            "periodo": {
                "inicio": min(nf["data_emissao"] for nf in notas_fiscais).isoformat(),
                "fim": max(nf["data_emissao"] for nf in notas_fiscais).isoformat()
            },
            "entradas": {
                "base_icms": float(base_icms_entradas),
                "valor_icms": float(icms_entradas)
            },
            "saidas": {
                "base_icms": float(base_icms_saidas),
                "valor_icms": float(icms_saidas)
            },
            "apuracao": {
                "saldo_credor": float(saldo_credor),
                "saldo_devedor": float(saldo_devedor),
                "icms_a_recolher": float(saldo_credor)
            },
            "total_notas": len(notas_fiscais)
        }

        logger.info(
            f"Relatório de apuração gerado - "
            f"ICMS a recolher: R$ {saldo_credor:.2f}"
        )

        return relatorio


# Instância global do serviço
sped_service = SPEDService()
