"""
Service para integração de frete no módulo de vendas
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.integrations.correios import CorreiosClient
from app.integrations.melhorenvio import MelhorEnvioClient
from app.core.config import settings

logger = logging.getLogger(__name__)


class FreteVendasService:
    """
    Service para calcular e gerenciar frete nas vendas

    Funcionalidades:
    - Cálculo de frete com múltiplos provedores
    - Seleção do melhor frete
    - Validação de CEP
    - Geração de etiquetas
    """

    def __init__(self):
        """Inicializa clientes de frete"""
        self.correios = CorreiosClient()

        # Melhor Envio (se configurado)
        me_client_id = getattr(settings, 'MELHOR_ENVIO_CLIENT_ID', None)
        me_secret = getattr(settings, 'MELHOR_ENVIO_CLIENT_SECRET', None)

        if me_client_id and me_secret:
            self.melhor_envio = MelhorEnvioClient(
                client_id=me_client_id,
                client_secret=me_secret
            )
        else:
            self.melhor_envio = None

    async def calcular_frete_para_venda(
        self,
        cep_origem: str,
        cep_destino: str,
        itens: List[Dict[str, Any]],
        valor_total: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calcula frete para uma venda com múltiplos itens

        Args:
            cep_origem: CEP de origem (loja)
            cep_destino: CEP de destino (cliente)
            itens: Lista de itens da venda com peso e dimensões
            valor_total: Valor total da venda (para seguro)

        Returns:
            Opções de frete disponíveis ordenadas por preço
        """
        logger.info(f"Calculando frete - Origem: {cep_origem}, Destino: {cep_destino}, Itens: {len(itens)}")

        # Calcular totais dos itens
        peso_total, dimensoes = self._calcular_totais_itens(itens)

        if peso_total <= 0:
            logger.warning("Peso total zero ou negativo")
            return {
                "erro": "Peso total inválido",
                "opcoes": []
            }

        opcoes_frete = []

        # 1. Calcular com Correios
        try:
            correios_result = await self.correios.calcular_frete(
                cep_origem=cep_origem,
                cep_destino=cep_destino,
                peso=peso_total,
                formato=1,  # Caixa/pacote
                comprimento=dimensoes['comprimento'],
                altura=dimensoes['altura'],
                largura=dimensoes['largura']
            )

            if "servicos" in correios_result:
                for servico in correios_result["servicos"]:
                    if servico.get("erro") is None:
                        opcoes_frete.append({
                            "provedor": "correios",
                            "servico": servico["nome"],
                            "codigo": servico["codigo"],
                            "valor": float(servico["valor"]),
                            "prazo_entrega": servico["prazo_entrega"],
                            "tipo": "pac" if "PAC" in servico["nome"] else "sedex"
                        })
        except Exception as e:
            logger.error(f"Erro ao calcular frete Correios: {str(e)}")

        # 2. Calcular com Melhor Envio (se disponível)
        if self.melhor_envio:
            try:
                me_result = await self.melhor_envio.calcular_frete(
                    cep_origem=cep_origem,
                    cep_destino=cep_destino,
                    peso=peso_total,
                    altura=dimensoes['altura'],
                    largura=dimensoes['largura'],
                    comprimento=dimensoes['comprimento'],
                    valor_declarado=valor_total
                )

                for opcao in me_result:
                    if opcao.get("error") is None:
                        opcoes_frete.append({
                            "provedor": "melhor_envio",
                            "servico": opcao["name"],
                            "transportadora": opcao.get("company", {}).get("name", "N/A"),
                            "valor": float(opcao["price"]),
                            "prazo_entrega": opcao["delivery_time"],
                            "id_servico": opcao["id"]
                        })
            except Exception as e:
                logger.error(f"Erro ao calcular frete Melhor Envio: {str(e)}")

        # Ordenar por preço (mais barato primeiro)
        opcoes_frete.sort(key=lambda x: x["valor"])

        # Adicionar informações extras
        resultado = {
            "cep_origem": cep_origem,
            "cep_destino": cep_destino,
            "peso_total_kg": peso_total,
            "dimensoes": dimensoes,
            "quantidade_opcoes": len(opcoes_frete),
            "opcoes": opcoes_frete,
            "recomendacao": self._obter_recomendacao(opcoes_frete)
        }

        logger.info(f"Frete calculado: {len(opcoes_frete)} opções disponíveis")
        return resultado

    async def validar_cep(self, cep: str) -> Dict[str, Any]:
        """
        Valida um CEP e retorna informações do endereço

        Args:
            cep: CEP a validar

        Returns:
            Informações do CEP ou erro
        """
        try:
            resultado = await self.correios.consultar_cep(cep)

            if "erro" in resultado:
                return {
                    "valido": False,
                    "erro": "CEP não encontrado"
                }

            return {
                "valido": True,
                "cep": resultado["cep"],
                "logradouro": resultado.get("logradouro", ""),
                "bairro": resultado.get("bairro", ""),
                "cidade": resultado.get("localidade", ""),
                "estado": resultado.get("uf", ""),
                "complemento": resultado.get("complemento", "")
            }
        except Exception as e:
            logger.error(f"Erro ao validar CEP {cep}: {str(e)}")
            return {
                "valido": False,
                "erro": str(e)
            }

    async def gerar_etiqueta_frete(
        self,
        venda_id: int,
        opcao_frete: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Gera etiqueta de frete após venda confirmada

        Args:
            venda_id: ID da venda
            opcao_frete: Opção de frete selecionada

        Returns:
            Dados da etiqueta gerada
        """
        logger.info(f"Gerando etiqueta de frete para venda {venda_id}")

        provedor = opcao_frete.get("provedor")

        if provedor == "melhor_envio" and self.melhor_envio:
            # TODO: Implementar fluxo completo:
            # 1. Criar carrinho
            # 2. Fazer checkout
            # 3. Gerar etiqueta PDF
            logger.info("Geração de etiqueta Melhor Envio (implementação completa pendente)")
            return {
                "sucesso": False,
                "mensagem": "Geração de etiqueta Melhor Envio será implementada com dados reais da venda"
            }

        elif provedor == "correios":
            # TODO: Integração com API dos Correios para etiquetas
            logger.info("Geração de etiqueta Correios (requer contrato)")
            return {
                "sucesso": False,
                "mensagem": "Geração de etiqueta Correios requer contrato e integração específica"
            }

        return {
            "sucesso": False,
            "erro": f"Provedor {provedor} não suportado para geração de etiquetas"
        }

    def _calcular_totais_itens(
        self,
        itens: List[Dict[str, Any]]
    ) -> tuple[float, Dict[str, float]]:
        """
        Calcula peso total e dimensões a partir dos itens

        Args:
            itens: Lista de itens com peso e dimensões

        Returns:
            Tupla (peso_total, dimensoes)
        """
        peso_total = 0.0
        altura_max = 2.0  # cm (mínimo)
        largura_max = 11.0  # cm (mínimo)
        comprimento_total = 0.0

        for item in itens:
            quantidade = item.get("quantidade", 1)

            # Peso
            peso_item = item.get("peso", 0.1)  # kg, default 100g
            peso_total += peso_item * quantidade

            # Dimensões (assumir empilhamento)
            altura_item = item.get("altura", 2.0)  # cm
            largura_item = item.get("largura", 11.0)  # cm
            comprimento_item = item.get("comprimento", 16.0)  # cm

            altura_max = max(altura_max, altura_item)
            largura_max = max(largura_max, largura_item)

            # Somar comprimentos (empilhamento)
            comprimento_total += comprimento_item * quantidade

        # Limites dos Correios
        comprimento_final = min(comprimento_total, 105.0)  # Máximo 105cm
        altura_final = min(altura_max, 105.0)
        largura_final = min(largura_max, 105.0)

        return peso_total, {
            "altura": altura_final,
            "largura": largura_final,
            "comprimento": comprimento_final
        }

    def _obter_recomendacao(
        self,
        opcoes: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Retorna recomendação de melhor opção de frete

        Critérios:
        - Melhor custo-benefício (preço vs prazo)
        - Confiabilidade do provedor

        Args:
            opcoes: Lista de opções de frete

        Returns:
            Melhor opção recomendada ou None
        """
        if not opcoes:
            return None

        # Opção mais barata
        mais_barata = opcoes[0]

        # Se diferença de preço é pequena (<10%), preferir prazo menor
        for opcao in opcoes[1:]:
            diferenca_preco = abs(opcao["valor"] - mais_barata["valor"]) / mais_barata["valor"]

            if diferenca_preco < 0.10:  # Menos de 10% de diferença
                if opcao["prazo_entrega"] < mais_barata["prazo_entrega"]:
                    mais_barata = opcao

        return {
            "opcao": mais_barata,
            "motivo": "Melhor custo-benefício (preço e prazo)",
            "economia": None  # Pode calcular economia vs outras opções
        }

    async def obter_rastreamento(
        self,
        codigo_rastreio: str,
        provedor: str
    ) -> Dict[str, Any]:
        """
        Obtém rastreamento de envio

        Args:
            codigo_rastreio: Código de rastreamento
            provedor: Provedor do frete (correios, melhor_envio)

        Returns:
            Informações de rastreamento
        """
        logger.info(f"Rastreando envio: {codigo_rastreio} ({provedor})")

        if provedor == "melhor_envio" and self.melhor_envio:
            try:
                resultado = await self.melhor_envio.rastrear_envio(codigo_rastreio)
                return {
                    "sucesso": True,
                    "codigo": codigo_rastreio,
                    "provedor": provedor,
                    "status": resultado.get("status"),
                    "eventos": resultado.get("tracking", {}).get("history", [])
                }
            except Exception as e:
                logger.error(f"Erro ao rastrear Melhor Envio: {str(e)}")
                return {
                    "sucesso": False,
                    "erro": str(e)
                }

        elif provedor == "correios":
            # TODO: Implementar rastreamento Correios
            return {
                "sucesso": False,
                "mensagem": "Rastreamento Correios será implementado"
            }

        return {
            "sucesso": False,
            "erro": f"Provedor {provedor} não suportado"
        }
