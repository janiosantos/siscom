"""
Router para integrações de Marketplaces (Mercado Livre)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from decimal import Decimal
from pydantic import BaseModel, Field

from app.modules.auth.dependencies import get_current_user
from app.integrations.mercadolivre import MercadoLivreClient
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/marketplace", tags=["Marketplaces"])


# Schemas
class CriarAnuncioRequest(BaseModel):
    """Schema para criar anúncio"""
    titulo: str = Field(..., min_length=1, max_length=60, description="Título do anúncio")
    categoria_id: str = Field(..., description="ID da categoria do Mercado Livre")
    preco: Decimal = Field(..., gt=0, description="Preço do produto")
    quantidade: int = Field(..., gt=0, description="Quantidade disponível")
    condicao: str = Field(..., description="Condição (new ou used)")
    descricao: str = Field(..., min_length=1, description="Descrição do produto")
    imagens: List[str] = Field(..., min_items=1, description="URLs das imagens")
    atributos: Optional[List[Dict[str, Any]]] = Field(None, description="Atributos da categoria")


class AtualizarEstoqueRequest(BaseModel):
    """Schema para atualizar estoque"""
    quantidade: int = Field(..., ge=0, description="Nova quantidade")


class EnviarMensagemRequest(BaseModel):
    """Schema para enviar mensagem"""
    mensagem: str = Field(..., min_length=1, description="Texto da mensagem")


# Helper para obter client do ML
def get_ml_client() -> MercadoLivreClient:
    """Retorna client do Mercado Livre configurado"""
    client_id = getattr(settings, 'MERCADO_LIVRE_CLIENT_ID', None)
    client_secret = getattr(settings, 'MERCADO_LIVRE_CLIENT_SECRET', None)

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais do Mercado Livre não configuradas"
        )

    # TODO: Buscar access_token e refresh_token do banco de dados do usuário
    # Por enquanto, vazio (usuário precisa fazer OAuth primeiro)
    return MercadoLivreClient(
        client_id=client_id,
        client_secret=client_secret
    )


# Endpoints OAuth
@router.get("/mercadolivre/auth/url")
async def obter_url_autorizacao(
    redirect_uri: str = Query(..., description="URI de redirecionamento"),
    current_user=Depends(get_current_user)
):
    """
    Obtém URL para autorização no Mercado Livre

    O usuário deve acessar esta URL para autorizar a aplicação.
    Após autorizar, será redirecionado para redirect_uri com um code.
    """
    client_id = getattr(settings, 'MERCADO_LIVRE_CLIENT_ID', None)

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MERCADO_LIVRE_CLIENT_ID não configurado"
        )

    url = (
        f"https://auth.mercadolivre.com.br/authorization?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
    )

    return {
        "authorization_url": url,
        "redirect_uri": redirect_uri,
        "instrucoes": "Acesse a URL e autorize a aplicação. Você será redirecionado com um 'code' que deve ser usado no endpoint /mercadolivre/auth/token"
    }


@router.post("/mercadolivre/auth/token")
async def obter_access_token(
    code: str = Query(..., description="Código de autorização"),
    redirect_uri: str = Query(..., description="URI de redirecionamento"),
    current_user=Depends(get_current_user)
):
    """
    Obtém access token usando código de autorização

    Use o 'code' recebido após autorização para obter os tokens.
    Salve os tokens retornados para uso posterior.
    """
    logger.info(f"Obtendo access token ML - Usuário: {current_user.id}")

    try:
        client = get_ml_client()

        resultado = await client.obter_access_token(
            code=code,
            redirect_uri=redirect_uri
        )

        # TODO: Salvar access_token e refresh_token no banco de dados do usuário

        return {
            **resultado,
            "instrucao": "Salve estes tokens de forma segura. Use o access_token nos próximos endpoints."
        }

    except Exception as e:
        logger.error(f"Erro ao obter access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter access token: {str(e)}"
        )


@router.post("/mercadolivre/auth/refresh")
async def atualizar_access_token(
    current_user=Depends(get_current_user)
):
    """
    Atualiza access token usando refresh token

    Use quando o access token expirar.
    """
    logger.info(f"Atualizando access token ML - Usuário: {current_user.id}")

    try:
        client = get_ml_client()

        # TODO: Buscar refresh_token do banco de dados
        # client.refresh_token = user.ml_refresh_token

        resultado = await client.atualizar_access_token()

        # TODO: Atualizar tokens no banco de dados

        return resultado

    except Exception as e:
        logger.error(f"Erro ao atualizar access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar access token: {str(e)}"
        )


# Endpoints Anúncios
@router.post("/mercadolivre/anuncios")
async def criar_anuncio(
    dados: CriarAnuncioRequest,
    current_user=Depends(get_current_user)
):
    """
    Cria um novo anúncio no Mercado Livre

    Requer access_token válido. Faça OAuth antes.
    """
    logger.info(f"Criando anúncio ML - Usuário: {current_user.id}, Título: {dados.titulo}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        # client.access_token = user.ml_access_token

        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro usando /mercadolivre/auth/url"
            )

        resultado = await client.criar_anuncio(
            titulo=dados.titulo,
            categoria_id=dados.categoria_id,
            preco=dados.preco,
            quantidade=dados.quantidade,
            condicao=dados.condicao,
            descricao=dados.descricao,
            imagens=dados.imagens,
            atributos=dados.atributos
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar anúncio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar anúncio: {str(e)}"
        )


@router.put("/mercadolivre/anuncios/{item_id}/estoque")
async def atualizar_estoque(
    item_id: str,
    dados: AtualizarEstoqueRequest,
    current_user=Depends(get_current_user)
):
    """
    Atualiza estoque de um anúncio

    Sincroniza quantidade disponível com o Mercado Livre.
    """
    logger.info(f"Atualizando estoque ML - Item: {item_id}, Quantidade: {dados.quantidade}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro"
            )

        resultado = await client.atualizar_estoque(
            item_id=item_id,
            quantidade=dados.quantidade
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao atualizar estoque: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar estoque: {str(e)}"
        )


@router.put("/mercadolivre/anuncios/{item_id}/pausar")
async def pausar_anuncio(
    item_id: str,
    current_user=Depends(get_current_user)
):
    """
    Pausa um anúncio

    O anúncio ficará invisível para compradores.
    """
    logger.info(f"Pausando anúncio ML - Item: {item_id}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro"
            )

        resultado = await client.pausar_anuncio(item_id)

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao pausar anúncio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao pausar anúncio: {str(e)}"
        )


# Endpoints Vendas
@router.get("/mercadolivre/vendas")
async def listar_vendas(
    seller_id: str = Query(..., description="ID do vendedor"),
    status_venda: Optional[str] = Query(None, description="Filtrar por status"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    current_user=Depends(get_current_user)
):
    """
    Lista vendas do Mercado Livre

    Retorna pedidos recebidos com paginação.
    """
    logger.info(f"Listando vendas ML - Seller: {seller_id}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro"
            )

        resultado = await client.listar_vendas(
            seller_id=seller_id,
            status=status_venda,
            offset=offset,
            limit=limit
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao listar vendas: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar vendas: {str(e)}"
        )


@router.get("/mercadolivre/vendas/{order_id}")
async def obter_detalhes_venda(
    order_id: str,
    current_user=Depends(get_current_user)
):
    """
    Obtém detalhes completos de uma venda

    Retorna informações sobre pedido, pagamento e envio.
    """
    logger.info(f"Obtendo detalhes da venda ML: {order_id}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro"
            )

        resultado = await client.obter_detalhes_venda(order_id)

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter detalhes da venda: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter detalhes da venda: {str(e)}"
        )


# Endpoints Mensagens
@router.post("/mercadolivre/mensagens/{order_id}/{comprador_id}")
async def enviar_mensagem(
    order_id: str,
    comprador_id: str,
    dados: EnviarMensagemRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia mensagem para o comprador

    Use para comunicação sobre o pedido.
    """
    logger.info(f"Enviando mensagem ML - Order: {order_id}, Comprador: {comprador_id}")

    try:
        client = get_ml_client()

        # TODO: Buscar access_token do banco de dados
        if not client.access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Faça OAuth primeiro"
            )

        resultado = await client.enviar_mensagem(
            comprador_id=comprador_id,
            order_id=order_id,
            mensagem=dados.mensagem
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar mensagem: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Verifica se as integrações de marketplace estão configuradas

    Retorna status de configuração do Mercado Livre.
    """
    ml_configurado = bool(
        getattr(settings, 'MERCADO_LIVRE_CLIENT_ID', None) and
        getattr(settings, 'MERCADO_LIVRE_CLIENT_SECRET', None)
    )

    return {
        "status": "ok" if ml_configurado else "sem_configuracao",
        "mercado_livre": {
            "configurado": ml_configurado,
            "oauth_required": True,
            "instrucao": "Use /mercadolivre/auth/url para iniciar OAuth" if ml_configurado else "Configure MERCADO_LIVRE_CLIENT_ID e MERCADO_LIVRE_CLIENT_SECRET"
        }
    }
