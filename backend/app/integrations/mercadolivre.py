"""
Cliente para API do Mercado Livre
"""
import logging
import httpx
from typing import Dict, Any, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class MercadoLivreClient:
    """
    Client para integração com API do Mercado Livre

    Funcionalidades:
    - Listagem de produtos
    - Gerenciamento de anúncios
    - Processamento de vendas
    - Envio de mensagens
    - Atualização de estoque
    """

    def __init__(self, client_id: str, client_secret: str, access_token: str = None, refresh_token: str = None):
        """
        Inicializa client do Mercado Livre

        Args:
            client_id: Client ID da aplicação
            client_secret: Client Secret da aplicação
            access_token: Access token OAuth (opcional)
            refresh_token: Refresh token OAuth (opcional)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.base_url = "https://api.mercadolibre.com"

    async def obter_access_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Obtém access token via código de autorização (OAuth)

        Args:
            code: Código de autorização obtido na tela de autorização
            redirect_uri: URI de redirecionamento configurada

        Returns:
            Tokens de acesso e atualização
        """
        logger.info("Obtendo access token do Mercado Livre")

        url = f"{self.base_url}/oauth/token"

        payload = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

                logger.info("Access token obtido com sucesso")

                return {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_in": data.get("expires_in"),
                    "user_id": data.get("user_id")
                }

            except Exception as e:
                logger.error(f"Erro ao obter access token: {str(e)}")
                raise

    async def atualizar_access_token(self) -> Dict[str, Any]:
        """
        Atualiza access token usando refresh token

        Returns:
            Novos tokens
        """
        if not self.refresh_token:
            raise ValueError("Refresh token não configurado")

        logger.info("Atualizando access token")

        url = f"{self.base_url}/oauth/token"

        payload = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")

                logger.info("Access token atualizado com sucesso")

                return {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_in": data.get("expires_in")
                }

            except Exception as e:
                logger.error(f"Erro ao atualizar access token: {str(e)}")
                raise

    async def criar_anuncio(
        self,
        titulo: str,
        categoria_id: str,
        preco: Decimal,
        quantidade: int,
        condicao: str,  # new ou used
        descricao: str,
        imagens: List[str],
        atributos: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Cria um novo anúncio no Mercado Livre

        Args:
            titulo: Título do anúncio
            categoria_id: ID da categoria
            preco: Preço do produto
            quantidade: Quantidade disponível
            condicao: Condição do produto (new ou used)
            descricao: Descrição do produto
            imagens: Lista de URLs das imagens
            atributos: Lista de atributos específicos da categoria

        Returns:
            Dados do anúncio criado
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Criando anúncio: {titulo}")

        url = f"{self.base_url}/items"

        payload = {
            "title": titulo,
            "category_id": categoria_id,
            "price": float(preco),
            "currency_id": "BRL",
            "available_quantity": quantidade,
            "buying_mode": "buy_it_now",
            "condition": condicao,
            "listing_type_id": "gold_special",  # Tipo de anúncio
            "description": {"plain_text": descricao},
            "pictures": [{"source": url} for url in imagens]
        }

        if atributos:
            payload["attributes"] = atributos

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Anúncio criado - ID: {data.get('id')}, Permalink: {data.get('permalink')}")

                return {
                    "id": data.get("id"),
                    "permalink": data.get("permalink"),
                    "status": data.get("status"),
                    "titulo": data.get("title"),
                    "preco": data.get("price")
                }

            except httpx.HTTPStatusError as e:
                logger.error(f"Erro ao criar anúncio: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Erro ao criar anúncio: {str(e)}")
                raise

    async def atualizar_estoque(self, item_id: str, quantidade: int) -> Dict[str, Any]:
        """
        Atualiza a quantidade disponível de um anúncio

        Args:
            item_id: ID do anúncio
            quantidade: Nova quantidade

        Returns:
            Dados atualizados
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Atualizando estoque do item {item_id} para {quantidade}")

        url = f"{self.base_url}/items/{item_id}"

        payload = {
            "available_quantity": quantidade
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Estoque atualizado - ID: {item_id}, Nova quantidade: {quantidade}")

                return {
                    "id": data.get("id"),
                    "quantidade": data.get("available_quantity"),
                    "status": data.get("status")
                }

            except Exception as e:
                logger.error(f"Erro ao atualizar estoque: {str(e)}")
                raise

    async def pausar_anuncio(self, item_id: str) -> Dict[str, Any]:
        """
        Pausa um anúncio

        Args:
            item_id: ID do anúncio

        Returns:
            Status do anúncio
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Pausando anúncio: {item_id}")

        url = f"{self.base_url}/items/{item_id}"

        payload = {
            "status": "paused"
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.put(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Anúncio pausado - ID: {item_id}")

                return {
                    "id": data.get("id"),
                    "status": data.get("status")
                }

            except Exception as e:
                logger.error(f"Erro ao pausar anúncio: {str(e)}")
                raise

    async def listar_vendas(
        self,
        seller_id: str,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Lista vendas do seller

        Args:
            seller_id: ID do vendedor
            status: Filtrar por status (opcional)
            offset: Offset para paginação
            limit: Limite de resultados

        Returns:
            Lista de vendas
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Listando vendas do seller {seller_id}")

        url = f"{self.base_url}/orders/search"

        params = {
            "seller": seller_id,
            "offset": offset,
            "limit": limit
        }

        if status:
            params["order.status"] = status

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers, params=params)
                response.raise_for_status()

                data = response.json()

                vendas = []
                for ordem in data.get("results", []):
                    vendas.append({
                        "id": ordem.get("id"),
                        "status": ordem.get("status"),
                        "data": ordem.get("date_created"),
                        "total": ordem.get("total_amount"),
                        "comprador_id": ordem.get("buyer", {}).get("id"),
                        "itens": len(ordem.get("order_items", []))
                    })

                logger.info(f"Encontradas {len(vendas)} vendas")

                return {
                    "total": data.get("paging", {}).get("total"),
                    "vendas": vendas,
                    "paginacao": data.get("paging")
                }

            except Exception as e:
                logger.error(f"Erro ao listar vendas: {str(e)}")
                raise

    async def obter_detalhes_venda(self, order_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes completos de uma venda

        Args:
            order_id: ID da ordem

        Returns:
            Detalhes da venda
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Obtendo detalhes da venda: {order_id}")

        url = f"{self.base_url}/orders/{order_id}"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Detalhes obtidos - Ordem: {order_id}, Status: {data.get('status')}")

                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "data_criacao": data.get("date_created"),
                    "data_fechamento": data.get("date_closed"),
                    "total": data.get("total_amount"),
                    "comprador": data.get("buyer"),
                    "itens": data.get("order_items"),
                    "pagamentos": data.get("payments"),
                    "envio": data.get("shipping")
                }

            except Exception as e:
                logger.error(f"Erro ao obter detalhes da venda: {str(e)}")
                raise

    async def enviar_mensagem(
        self,
        comprador_id: str,
        order_id: str,
        mensagem: str
    ) -> Dict[str, Any]:
        """
        Envia mensagem para o comprador

        Args:
            comprador_id: ID do comprador
            order_id: ID da ordem
            mensagem: Texto da mensagem

        Returns:
            Dados da mensagem enviada
        """
        if not self.access_token:
            raise ValueError("Access token não configurado")

        logger.info(f"Enviando mensagem para comprador {comprador_id}")

        url = f"{self.base_url}/messages/packs/{order_id}/sellers/{comprador_id}"

        payload = {
            "from": {"user_id": "me"},
            "to": {"user_id": comprador_id},
            "text": mensagem
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()

                data = response.json()

                logger.info(f"Mensagem enviada com sucesso")

                return {
                    "sucesso": True,
                    "message_id": data.get("id"),
                    "status": data.get("status")
                }

            except Exception as e:
                logger.error(f"Erro ao enviar mensagem: {str(e)}")
                raise
