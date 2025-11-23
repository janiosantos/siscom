"""
Integração com Sicoob (Cooperativa de Crédito)
Gateway focado em PIX + Boleto
"""
import httpx
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime, timedelta
import base64
import hashlib


class SicoobEnvironment(str, Enum):
    """Ambientes Sicoob"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class SicoobClient:
    """
    Cliente para integração com Sicoob API

    Foco: PIX (QR Code dinâmico/estático) + Boleto
    Documentação: https://developers.sicoob.com.br
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        certificate_path: Optional[str] = None,
        environment: SicoobEnvironment = SicoobEnvironment.SANDBOX
    ):
        self.client_id = client_id or "CLIENT_ID_SANDBOX"
        self.client_secret = client_secret or "CLIENT_SECRET_SANDBOX"
        self.certificate_path = certificate_path
        self.environment = environment

        # URLs por ambiente
        if environment == SicoobEnvironment.SANDBOX:
            self.base_url = "https://api-sandbox.sicoob.com.br"
            self.auth_url = "https://auth-sandbox.sicoob.com.br/auth/realms/cooperado/protocol/openid-connect/token"
        else:
            self.base_url = "https://api.sicoob.com.br"
            self.auth_url = "https://auth.sicoob.com.br/auth/realms/cooperado/protocol/openid-connect/token"

        self._access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        """
        Obtém access token OAuth2
        """
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.auth_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "scope": "cob.write cob.read cobv.write cobv.read pix.write pix.read"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            return self._access_token

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Faz requisição autenticada para API Sicoob
        """
        token = await self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()

            # Algumas respostas não têm body
            if response.status_code == 204:
                return {}

            return response.json()

    # ============================================================================
    # PIX - COBRANÇA IMEDIATA (COB)
    # ============================================================================

    async def create_pix_charge(
        self,
        amount: float,
        txid: Optional[str] = None,
        payer_cpf: Optional[str] = None,
        payer_name: Optional[str] = None,
        expiration_seconds: int = 1800,
        info_adicional: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria cobrança PIX imediata (QR Code dinâmico)

        Args:
            amount: Valor em reais
            txid: Transaction ID (gerado automaticamente se não fornecido)
            payer_cpf: CPF/CNPJ do pagador
            payer_name: Nome do pagador
            expiration_seconds: Tempo de expiração (padrão 30min)
            info_adicional: Informação adicional

        Returns:
            Dict com qrcode (base64), payload_code (copia e cola), location, txid
        """
        if not txid:
            # Gerar txid aleatório de 32 caracteres
            import uuid
            txid = uuid.uuid4().hex

        # Calcular tempo de expiração
        expiration_time = int((datetime.now() + timedelta(seconds=expiration_seconds)).timestamp())

        payload = {
            "calendario": {
                "expiracao": expiration_seconds
            },
            "valor": {
                "original": f"{amount:.2f}"
            },
            "chave": self.client_id,  # Chave PIX da cooperativa
        }

        # Informações do pagador (opcional)
        if payer_cpf or payer_name:
            payload["devedor"] = {}
            if payer_cpf:
                if len(payer_cpf) == 11:
                    payload["devedor"]["cpf"] = payer_cpf
                else:
                    payload["devedor"]["cnpj"] = payer_cpf
            if payer_name:
                payload["devedor"]["nome"] = payer_name

        # Informação adicional
        if info_adicional:
            payload["solicitacaoPagador"] = info_adicional

        response = await self._make_request(
            "PUT",
            f"/pix/api/v2/cob/{txid}",
            data=payload
        )

        return response

    async def create_pix_static_qr(
        self,
        amount: Optional[float] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria QR Code PIX estático (valor fixo ou aberto)

        Args:
            amount: Valor em reais (None = valor aberto)
            description: Descrição da cobrança

        Returns:
            Dict com qrcode e payload_code
        """
        payload = {
            "chave": self.client_id
        }

        if amount is not None:
            payload["valor"] = {"original": f"{amount:.2f}"}

        if description:
            payload["infoAdicionais"] = [{"nome": "Descrição", "valor": description}]

        response = await self._make_request(
            "POST",
            "/pix/api/v2/cobv",
            data=payload
        )

        return response

    # ============================================================================
    # PIX - CONSULTAS
    # ============================================================================

    async def query_pix_charge(self, txid: str) -> Dict[str, Any]:
        """
        Consulta cobrança PIX por txid
        """
        return await self._make_request("GET", f"/pix/api/v2/cob/{txid}")

    async def query_pix_payment(self, e2e_id: str) -> Dict[str, Any]:
        """
        Consulta pagamento PIX recebido por E2E ID

        Args:
            e2e_id: End-to-End ID da transação PIX
        """
        return await self._make_request("GET", f"/pix/api/v2/pix/{e2e_id}")

    async def list_pix_charges(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[str] = None,
        page: int = 0,
        items_per_page: int = 100
    ) -> Dict[str, Any]:
        """
        Lista cobranças PIX em um período

        Args:
            start_date: Data inicial
            end_date: Data final
            status: Filtro de status (ATIVA, CONCLUIDA, REMOVIDA_PELO_USUARIO_RECEBEDOR, REMOVIDA_PELO_PSP)
            page: Página (pagination)
            items_per_page: Itens por página
        """
        params = {
            "inicio": start_date.isoformat(),
            "fim": end_date.isoformat(),
            "paginacao.paginaAtual": page,
            "paginacao.itensPorPagina": items_per_page
        }

        if status:
            params["status"] = status

        return await self._make_request("GET", "/pix/api/v2/cob", params=params)

    # ============================================================================
    # PIX - DEVOLUÇÃO
    # ============================================================================

    async def refund_pix_payment(
        self,
        e2e_id: str,
        refund_id: str,
        amount: float,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Solicita devolução de pagamento PIX

        Args:
            e2e_id: End-to-End ID da transação original
            refund_id: ID único da devolução
            amount: Valor a devolver
            reason: Motivo da devolução
        """
        payload = {
            "valor": f"{amount:.2f}"
        }

        if reason:
            payload["natureza"] = "ORIGINAL"  # ORIGINAL ou RETIRADA
            payload["descricao"] = reason

        return await self._make_request(
            "PUT",
            f"/pix/api/v2/pix/{e2e_id}/devolucao/{refund_id}",
            data=payload
        )

    # ============================================================================
    # BOLETO
    # ============================================================================

    async def create_boleto(
        self,
        amount: float,
        due_date: datetime,
        payer_name: str,
        payer_document: str,
        payer_address: Dict[str, str],
        description: Optional[str] = None,
        fine_percentage: float = 0.0,
        interest_percentage: float = 0.0
    ) -> Dict[str, Any]:
        """
        Cria boleto bancário

        Args:
            amount: Valor em reais
            due_date: Data de vencimento
            payer_name: Nome do pagador
            payer_document: CPF/CNPJ do pagador
            payer_address: Endereço do pagador (logradouro, cidade, uf, cep)
            description: Descrição
            fine_percentage: Percentual de multa após vencimento
            interest_percentage: Percentual de juros ao mês
        """
        payload = {
            "valor": amount,
            "dataVencimento": due_date.strftime("%Y-%m-%d"),
            "pagador": {
                "nome": payer_name,
                "numeroInscricao": payer_document,
                "tipoPessoa": "FISICA" if len(payer_document) == 11 else "JURIDICA",
                "endereco": payer_address
            }
        }

        if description:
            payload["descricao"] = description

        if fine_percentage > 0:
            payload["multa"] = {
                "tipo": "PERCENTUAL",
                "valor": fine_percentage
            }

        if interest_percentage > 0:
            payload["juros"] = {
                "tipo": "PERCENTUAL_MES",
                "valor": interest_percentage
            }

        return await self._make_request("POST", "/boleto/api/v1/boletos", data=payload)

    async def query_boleto(self, nosso_numero: str) -> Dict[str, Any]:
        """
        Consulta boleto por nosso número
        """
        return await self._make_request("GET", f"/boleto/api/v1/boletos/{nosso_numero}")

    async def cancel_boleto(self, nosso_numero: str) -> Dict[str, Any]:
        """
        Cancela boleto
        """
        return await self._make_request("DELETE", f"/boleto/api/v1/boletos/{nosso_numero}")

    # ============================================================================
    # UTILIDADES
    # ============================================================================

    def format_pix_status(self, status: str) -> str:
        """
        Formata status de cobrança PIX
        """
        status_map = {
            "ATIVA": "Ativa (Aguardando Pagamento)",
            "CONCLUIDA": "Concluída (Paga)",
            "REMOVIDA_PELO_USUARIO_RECEBEDOR": "Removida pelo Recebedor",
            "REMOVIDA_PELO_PSP": "Removida pelo PSP"
        }
        return status_map.get(status, status)

    def is_pix_paid(self, charge: Dict[str, Any]) -> bool:
        """
        Verifica se cobrança PIX foi paga
        """
        return charge.get("status") == "CONCLUIDA"

    def format_boleto_status(self, status: str) -> str:
        """
        Formata status de boleto
        """
        status_map = {
            "EMITIDO": "Emitido",
            "PAGO": "Pago",
            "CANCELADO": "Cancelado",
            "VENCIDO": "Vencido"
        }
        return status_map.get(status, status)
