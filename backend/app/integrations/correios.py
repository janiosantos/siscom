"""
Cliente para API dos Correios (cálculo de frete)
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CorreiosClient:
    """
    Client para integração com API dos Correios

    Funcionalidades:
    - Cálculo de frete (PAC, SEDEX)
    - Consulta de CEP
    - Rastreamento de encomendas
    """

    def __init__(self, usuario: str = None, senha: str = None):
        """
        Inicializa client dos Correios

        Args:
            usuario: Código administrativo dos Correios (opcional)
            senha: Senha dos Correios (opcional)
        """
        self.usuario = usuario or ""
        self.senha = senha or ""
        self.base_url = "https://ws.correios.com.br"

    async def calcular_frete(
        self,
        cep_origem: str,
        cep_destino: str,
        peso: float,
        formato: int = 1,  # 1=Caixa/Pacote, 2=Rolo/Prisma, 3=Envelope
        comprimento: float = 16,
        altura: float = 2,
        largura: float = 11,
        servicos: List[str] = None
    ) -> Dict[str, Any]:
        """
        Calcula o frete para os Correios

        Args:
            cep_origem: CEP de origem (8 dígitos)
            cep_destino: CEP de destino (8 dígitos)
            peso: Peso em kg
            formato: Formato da encomenda (1, 2 ou 3)
            comprimento: Comprimento em cm
            altura: Altura em cm
            largura: Largura em cm
            servicos: Lista de códigos de serviço (PAC=04510, SEDEX=04014)

        Returns:
            Dicionário com valores de frete por serviço
        """
        if servicos is None:
            servicos = ["04510", "04014"]  # PAC e SEDEX

        # Limpar CEPs
        cep_origem = cep_origem.replace("-", "").replace(".", "")
        cep_destino = cep_destino.replace("-", "").replace(".", "")

        logger.info(f"Calculando frete Correios - Origem: {cep_origem}, Destino: {cep_destino}, Peso: {peso}kg")

        resultados = []

        for codigo_servico in servicos:
            try:
                # Montar URL da API de cálculo de frete
                url = f"{self.base_url}/calculador/CalcPrecoPrazo.asmx/CalcPrecoPrazo"

                params = {
                    "nCdEmpresa": self.usuario,
                    "sDsSenha": self.senha,
                    "nCdServico": codigo_servico,
                    "sCepOrigem": cep_origem,
                    "sCepDestino": cep_destino,
                    "nVlPeso": str(peso),
                    "nCdFormato": str(formato),
                    "nVlComprimento": str(comprimento),
                    "nVlAltura": str(altura),
                    "nVlLargura": str(largura),
                    "nVlDiametro": "0",
                    "sCdMaoPropria": "N",
                    "nVlValorDeclarado": "0",
                    "sCdAvisoRecebimento": "N"
                }

                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()

                    # Parse XML response
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)

                    # Extrair dados do serviço
                    servico_data = root.find('.//cServico')
                    if servico_data is not None:
                        codigo = servico_data.find('Codigo').text
                        valor = servico_data.find('Valor').text.replace(',', '.')
                        prazo = servico_data.find('PrazoEntrega').text
                        erro = servico_data.find('Erro').text
                        msg_erro = servico_data.find('MsgErro').text if servico_data.find('MsgErro') is not None else ""

                        nome_servico = "PAC" if codigo == "04510" else "SEDEX" if codigo == "04014" else f"Serviço {codigo}"

                        resultado = {
                            "servico": nome_servico,
                            "codigo": codigo,
                            "valor": Decimal(valor) if erro == "0" else None,
                            "prazo_dias": int(prazo) if erro == "0" else None,
                            "erro": erro != "0",
                            "mensagem_erro": msg_erro if erro != "0" else None
                        }

                        resultados.append(resultado)

                        if erro == "0":
                            logger.info(f"Frete {nome_servico}: R$ {valor} - {prazo} dias")
                        else:
                            logger.warning(f"Erro ao calcular {nome_servico}: {msg_erro}")

            except Exception as e:
                logger.error(f"Erro ao calcular frete para serviço {codigo_servico}: {str(e)}")
                resultados.append({
                    "servico": f"Serviço {codigo_servico}",
                    "codigo": codigo_servico,
                    "valor": None,
                    "prazo_dias": None,
                    "erro": True,
                    "mensagem_erro": str(e)
                })

        return {
            "cep_origem": cep_origem,
            "cep_destino": cep_destino,
            "peso_kg": peso,
            "servicos": resultados
        }

    async def consultar_cep(self, cep: str) -> Dict[str, Any]:
        """
        Consulta informações de um CEP

        Args:
            cep: CEP a consultar (8 dígitos)

        Returns:
            Dados do endereço
        """
        cep = cep.replace("-", "").replace(".", "")
        logger.info(f"Consultando CEP: {cep}")

        url = f"https://viacep.com.br/ws/{cep}/json/"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                data = response.json()

                if "erro" in data:
                    logger.warning(f"CEP {cep} não encontrado")
                    return {
                        "cep": cep,
                        "erro": True,
                        "mensagem": "CEP não encontrado"
                    }

                logger.info(f"CEP {cep} encontrado: {data.get('localidade')}/{data.get('uf')}")

                return {
                    "cep": data.get("cep"),
                    "logradouro": data.get("logradouro"),
                    "complemento": data.get("complemento"),
                    "bairro": data.get("bairro"),
                    "cidade": data.get("localidade"),
                    "uf": data.get("uf"),
                    "ibge": data.get("ibge"),
                    "erro": False
                }

        except Exception as e:
            logger.error(f"Erro ao consultar CEP {cep}: {str(e)}")
            return {
                "cep": cep,
                "erro": True,
                "mensagem": str(e)
            }

    async def rastrear_encomenda(self, codigo_rastreio: str) -> Dict[str, Any]:
        """
        Rastreia uma encomenda dos Correios

        Args:
            codigo_rastreio: Código de rastreamento (13 caracteres)

        Returns:
            Status e histórico da encomenda
        """
        logger.info(f"Rastreando encomenda: {codigo_rastreio}")

        # API de rastreamento dos Correios
        url = f"{self.base_url}/service/rastro"

        # Nota: A API real dos Correios requer autenticação e tem formato específico
        # Esta é uma implementação simplificada

        try:
            # TODO: Implementar integração real com API de rastreamento
            # Por enquanto, retorna estrutura de exemplo

            logger.info(f"Rastreamento em desenvolvimento para: {codigo_rastreio}")

            return {
                "codigo": codigo_rastreio,
                "status": "em_desenvolvimento",
                "mensagem": "Funcionalidade de rastreamento em desenvolvimento",
                "eventos": []
            }

        except Exception as e:
            logger.error(f"Erro ao rastrear encomenda {codigo_rastreio}: {str(e)}")
            return {
                "codigo": codigo_rastreio,
                "erro": True,
                "mensagem": str(e)
            }
