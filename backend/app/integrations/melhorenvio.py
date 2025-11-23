"""
Cliente para API do Melhor Envio
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class MelhorEnvioClient:
    """
    Client para integração com API do Melhor Envio

    Funcionalidades:
    - Cálculo de frete (múltiplas transportadoras)
    - Geração de etiquetas
    - Rastreamento de encomendas
    - Checkout de frete
    """

    def __init__(self, client_id: str, client_secret: str, sandbox: bool = True):
        """
        Inicializa client do Melhor Envio

        Args:
            client_id: Client ID da aplicação
            client_secret: Client Secret da aplicação
            sandbox: Se True, usa ambiente de testes
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.sandbox = sandbox
        self.base_url = "https://sandbox.melhorenvio.com.br" if sandbox else "https://api.melhorenvio.com"
        self.access_token = None

    async def _get_access_token(self) -> str:
        """Obtém access token via OAuth2"""
        if self.access_token:
            return self.access_token

        logger.info("Obtendo access token do Melhor Envio")

        url = f"{self.base_url}/oauth/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "*"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()
                self.access_token = data.get("access_token")

                logger.info("Access token obtido com sucesso")
                return self.access_token

            except Exception as e:
                logger.error(f"Erro ao obter access token: {str(e)}")
                raise

    async def calcular_frete(
        self,
        cep_origem: str,
        cep_destino: str,
        peso: float,
        altura: float,
        largura: float,
        comprimento: float,
        valor_declarado: Optional[Decimal] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula frete com múltiplas transportadoras

        Args:
            cep_origem: CEP de origem
            cep_destino: CEP de destino
            peso: Peso em kg
            altura: Altura em cm
            largura: Largura em cm
            comprimento: Comprimento em cm
            valor_declarado: Valor declarado da mercadoria

        Returns:
            Lista de cotações de diferentes transportadoras
        """
        token = await self._get_access_token()

        # Limpar CEPs
        cep_origem = cep_origem.replace("-", "").replace(".", "")
        cep_destino = cep_destino.replace("-", "").replace(".", "")

        logger.info(f"Calculando frete ME - Origem: {cep_origem}, Destino: {cep_destino}, Peso: {peso}kg")

        url = f"{self.base_url}/api/v2/me/shipment/calculate"

        payload = {
            "from": {"postal_code": cep_origem},
            "to": {"postal_code": cep_destino},
            "package": {
                "weight": peso,
                "width": largura,
                "height": altura,
                "length": comprimento
            }
        }

        if valor_declarado:
            payload["options"] = {
                "insurance_value": float(valor_declarado),
                "receipt": False,
                "own_hand": False
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                cotacoes = response.json()
                resultados = []

                for cotacao in cotacoes:
                    if cotacao.get("error"):
                        logger.warning(f"Erro na cotação {cotacao.get('name')}: {cotacao.get('error')}")
                        continue

                    resultado = {
                        "transportadora": cotacao.get("company", {}).get("name"),
                        "servico": cotacao.get("name"),
                        "servico_id": cotacao.get("id"),
                        "valor": Decimal(str(cotacao.get("price", 0))),
                        "prazo_dias": cotacao.get("delivery_time"),
                        "prazo_range": {
                            "min": cotacao.get("delivery_range", {}).get("min"),
                            "max": cotacao.get("delivery_range", {}).get("max")
                        },
                        "valor_seguro": Decimal(str(cotacao.get("insurance_value", 0))),
                        "desconto": Decimal(str(cotacao.get("discount", 0))),
                        "logo": cotacao.get("company", {}).get("picture")
                    }

                    resultados.append(resultado)

                    logger.info(
                        f"Frete {resultado['transportadora']} - {resultado['servico']}: "
                        f"R$ {resultado['valor']} ({resultado['prazo_dias']} dias)"
                    )

                # Ordenar por valor
                resultados.sort(key=lambda x: x["valor"])

                return resultados

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro HTTP ao calcular frete: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Erro ao calcular frete: {str(e)}")
                raise

    async def criar_carrinho(
        self,
        cotacao_id: int,
        volumes: List[Dict[str, Any]],
        remetente: Dict[str, Any],
        destinatario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Adiciona envio ao carrinho para posterior checkout

        Args:
            cotacao_id: ID da cotação escolhida
            volumes: Lista de volumes/pacotes
            remetente: Dados do remetente
            destinatario: Dados do destinatário

        Returns:
            Dados do envio adicionado ao carrinho
        """
        token = await self._get_access_token()

        logger.info(f"Criando envio no carrinho - Cotação ID: {cotacao_id}")

        url = f"{self.base_url}/api/v2/me/cart"

        payload = {
            "service": cotacao_id,
            "from": remetente,
            "to": destinatario,
            "volumes": volumes
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Envio adicionado ao carrinho: {data.get('id')}")

                return data

            except Exception as e:
                logger.error(f"Erro ao criar carrinho: {str(e)}")
                raise

    async def checkout(self, order_ids: List[str]) -> Dict[str, Any]:
        """
        Realiza checkout dos envios (gera etiquetas e efetua pagamento)

        Args:
            order_ids: IDs dos envios no carrinho

        Returns:
            Dados do checkout
        """
        token = await self._get_access_token()

        logger.info(f"Realizando checkout - Orders: {order_ids}")

        url = f"{self.base_url}/api/v2/me/shipment/checkout"

        payload = {
            "orders": order_ids
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Checkout realizado com sucesso: {data.get('purchase', {}).get('id')}")

                return data

            except Exception as e:
                logger.error(f"Erro ao realizar checkout: {str(e)}")
                raise

    async def gerar_etiqueta(self, order_id: str, mode: str = "private") -> bytes:
        """
        Gera etiqueta de envio em PDF

        Args:
            order_id: ID do envio
            mode: Modo de impressão (private ou public)

        Returns:
            PDF da etiqueta em bytes
        """
        token = await self._get_access_token()

        logger.info(f"Gerando etiqueta - Order: {order_id}")

        url = f"{self.base_url}/api/v2/me/shipment/print"

        payload = {
            "mode": mode,
            "orders": [order_id]
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()
                etiqueta_url = data.get("url")

                # Baixar PDF da etiqueta
                response_pdf = await client.get(etiqueta_url)
                response_pdf.raise_for_status()

                logger.info(f"Etiqueta gerada com sucesso")

                return response_pdf.content

            except Exception as e:
                logger.error(f"Erro ao gerar etiqueta: {str(e)}")
                raise

    async def rastrear_envio(self, order_id: str) -> Dict[str, Any]:
        """
        Rastreia um envio

        Args:
            order_id: ID do envio

        Returns:
            Status e eventos de rastreamento
        """
        token = await self._get_access_token()

        logger.info(f"Rastreando envio: {order_id}")

        url = f"{self.base_url}/api/v2/me/shipment/tracking"

        params = {"orders": order_id}

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Rastreamento obtido: {len(data)} eventos")

                return data

            except Exception as e:
                logger.error(f"Erro ao rastrear envio: {str(e)}")
                raise
