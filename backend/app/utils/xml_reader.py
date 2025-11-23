"""
Leitor de arquivos XML de NF-e
"""
import xmltodict
from typing import Dict, Any, List
from decimal import Decimal


class NFeXMLReader:
    """Leitor de XML de Nota Fiscal Eletrônica"""

    @staticmethod
    def parse_xml(xml_content: str) -> Dict[str, Any]:
        """
        Parse do conteúdo XML da NF-e

        Args:
            xml_content: Conteúdo do XML como string

        Returns:
            Dicionário com os dados da nota
        """
        data = xmltodict.parse(xml_content)
        return data

    @staticmethod
    def extract_nfe_data(xml_content: str) -> Dict[str, Any]:
        """
        Extrai dados principais da NF-e

        Args:
            xml_content: Conteúdo do XML

        Returns:
            Dicionário com dados estruturados
        """
        data = NFeXMLReader.parse_xml(xml_content)

        # Navega na estrutura do XML
        nfe = data.get("nfeProc", {}).get("NFe", {})
        inf_nfe = nfe.get("infNFe", {})

        # Dados do emitente (fornecedor)
        emit = inf_nfe.get("emit", {})
        fornecedor = {
            "cnpj": emit.get("CNPJ", ""),
            "razao_social": emit.get("xNome", ""),
            "fantasia": emit.get("xFant", ""),
            "ie": emit.get("IE", ""),
            "endereco": {
                "logradouro": emit.get("enderEmit", {}).get("xLgr", ""),
                "numero": emit.get("enderEmit", {}).get("nro", ""),
                "bairro": emit.get("enderEmit", {}).get("xBairro", ""),
                "municipio": emit.get("enderEmit", {}).get("xMun", ""),
                "uf": emit.get("enderEmit", {}).get("UF", ""),
                "cep": emit.get("enderEmit", {}).get("CEP", ""),
            },
        }

        # Dados da nota
        ide = inf_nfe.get("ide", {})
        nota_info = {
            "numero": ide.get("nNF", ""),
            "serie": ide.get("serie", ""),
            "data_emissao": ide.get("dhEmi", ""),
            "chave": inf_nfe.get("@Id", "").replace("NFe", ""),
        }

        # Totais
        total = inf_nfe.get("total", {}).get("ICMSTot", {})
        totais = {
            "valor_produtos": Decimal(total.get("vProd", "0")),
            "valor_frete": Decimal(total.get("vFrete", "0")),
            "valor_seguro": Decimal(total.get("vSeg", "0")),
            "valor_desconto": Decimal(total.get("vDesc", "0")),
            "valor_total": Decimal(total.get("vNF", "0")),
            "valor_icms": Decimal(total.get("vICMS", "0")),
            "valor_ipi": Decimal(total.get("vIPI", "0")),
        }

        # Produtos
        det = inf_nfe.get("det", [])
        if not isinstance(det, list):
            det = [det]

        produtos = []
        for item in det:
            prod = item.get("prod", {})
            produtos.append({
                "codigo": prod.get("cProd", ""),
                "ean": prod.get("cEAN", ""),
                "descricao": prod.get("xProd", ""),
                "ncm": prod.get("NCM", ""),
                "cfop": prod.get("CFOP", ""),
                "unidade": prod.get("uCom", ""),
                "quantidade": Decimal(prod.get("qCom", "0")),
                "valor_unitario": Decimal(prod.get("vUnCom", "0")),
                "valor_total": Decimal(prod.get("vProd", "0")),
            })

        return {
            "fornecedor": fornecedor,
            "nota": nota_info,
            "totais": totais,
            "produtos": produtos,
        }
