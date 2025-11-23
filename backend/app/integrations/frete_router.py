"""
Router para integrações de Frete (Correios e Melhor Envio)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field

from app.modules.auth.dependencies import get_current_user
from app.integrations.correios import CorreiosClient
from app.integrations.melhorenvio import MelhorEnvioClient
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/frete", tags=["Frete"])


# Schemas
class CalcularFreteRequest(BaseModel):
    """Schema para calcular frete"""
    cep_origem: str = Field(..., description="CEP de origem")
    cep_destino: str = Field(..., description="CEP de destino")
    peso: float = Field(..., gt=0, description="Peso em kg")
    altura: float = Field(default=2, gt=0, description="Altura em cm")
    largura: float = Field(default=11, gt=0, description="Largura em cm")
    comprimento: float = Field(default=16, gt=0, description="Comprimento em cm")
    valor_declarado: Optional[Decimal] = Field(None, description="Valor declarado (opcional)")


class ConsultarCEPResponse(BaseModel):
    """Response de consulta de CEP"""
    cep: str
    logradouro: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    ibge: Optional[str] = None
    erro: bool


# Endpoints Correios
@router.post("/correios/calcular")
async def calcular_frete_correios(
    dados: CalcularFreteRequest,
    current_user=Depends(get_current_user)
):
    """
    Calcula frete pelos Correios (PAC e SEDEX)

    Retorna valores e prazos de entrega para os serviços disponíveis.
    """
    logger.info(f"Calculando frete Correios - Usuário: {current_user.id}")

    try:
        usuario = getattr(settings, 'CORREIOS_USUARIO', None)
        senha = getattr(settings, 'CORREIOS_SENHA', None)

        client = CorreiosClient(usuario=usuario, senha=senha)

        resultado = await client.calcular_frete(
            cep_origem=dados.cep_origem,
            cep_destino=dados.cep_destino,
            peso=dados.peso,
            altura=dados.altura,
            largura=dados.largura,
            comprimento=dados.comprimento
        )

        return resultado

    except Exception as e:
        logger.error(f"Erro ao calcular frete Correios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular frete: {str(e)}"
        )


@router.get("/cep/{cep}")
async def consultar_cep(
    cep: str,
    current_user=Depends(get_current_user)
):
    """
    Consulta informações de um CEP

    Retorna endereço completo do CEP consultado.
    """
    logger.info(f"Consultando CEP: {cep}")

    try:
        client = CorreiosClient()
        resultado = await client.consultar_cep(cep)

        return ConsultarCEPResponse(**resultado)

    except Exception as e:
        logger.error(f"Erro ao consultar CEP: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar CEP: {str(e)}"
        )


# Endpoints Melhor Envio
@router.post("/melhorenvio/calcular")
async def calcular_frete_melhorenvio(
    dados: CalcularFreteRequest,
    current_user=Depends(get_current_user)
):
    """
    Calcula frete com múltiplas transportadoras via Melhor Envio

    Retorna cotações de várias transportadoras ordenadas por preço.
    """
    logger.info(f"Calculando frete Melhor Envio - Usuário: {current_user.id}")

    try:
        client_id = getattr(settings, 'MELHOR_ENVIO_CLIENT_ID', None)
        client_secret = getattr(settings, 'MELHOR_ENVIO_CLIENT_SECRET', None)

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciais do Melhor Envio não configuradas"
            )

        client = MelhorEnvioClient(
            client_id=client_id,
            client_secret=client_secret,
            sandbox=True
        )

        cotacoes = await client.calcular_frete(
            cep_origem=dados.cep_origem,
            cep_destino=dados.cep_destino,
            peso=dados.peso,
            altura=dados.altura,
            largura=dados.largura,
            comprimento=dados.comprimento,
            valor_declarado=dados.valor_declarado
        )

        return {
            "cep_origem": dados.cep_origem,
            "cep_destino": dados.cep_destino,
            "peso_kg": dados.peso,
            "total_cotacoes": len(cotacoes),
            "cotacoes": cotacoes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular frete Melhor Envio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular frete: {str(e)}"
        )


@router.get("/melhorenvio/rastreamento/{order_id}")
async def rastrear_envio_melhorenvio(
    order_id: str,
    current_user=Depends(get_current_user)
):
    """
    Rastreia um envio do Melhor Envio

    Retorna eventos de rastreamento da encomenda.
    """
    logger.info(f"Rastreando envio Melhor Envio: {order_id}")

    try:
        client_id = getattr(settings, 'MELHOR_ENVIO_CLIENT_ID', None)
        client_secret = getattr(settings, 'MELHOR_ENVIO_CLIENT_SECRET', None)

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Credenciais do Melhor Envio não configuradas"
            )

        client = MelhorEnvioClient(
            client_id=client_id,
            client_secret=client_secret,
            sandbox=True
        )

        rastreamento = await client.rastrear_envio(order_id)

        return rastreamento

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao rastrear envio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao rastrear envio: {str(e)}"
        )


@router.get("/comparar")
async def comparar_fretes(
    cep_origem: str,
    cep_destino: str,
    peso: float,
    altura: float = 2,
    largura: float = 11,
    comprimento: float = 16,
    current_user=Depends(get_current_user)
):
    """
    Compara fretes de Correios e Melhor Envio

    Retorna todas as opções de frete disponíveis em uma única chamada.
    """
    logger.info(f"Comparando fretes - Origem: {cep_origem}, Destino: {cep_destino}")

    resultados = {
        "cep_origem": cep_origem,
        "cep_destino": cep_destino,
        "peso_kg": peso,
        "correios": None,
        "melhor_envio": None,
        "erros": []
    }

    # Correios
    try:
        usuario = getattr(settings, 'CORREIOS_USUARIO', None)
        senha = getattr(settings, 'CORREIOS_SENHA', None)

        correios = CorreiosClient(usuario=usuario, senha=senha)
        resultados["correios"] = await correios.calcular_frete(
            cep_origem=cep_origem,
            cep_destino=cep_destino,
            peso=peso,
            altura=altura,
            largura=largura,
            comprimento=comprimento
        )
    except Exception as e:
        logger.error(f"Erro ao calcular Correios: {str(e)}")
        resultados["erros"].append(f"Correios: {str(e)}")

    # Melhor Envio
    try:
        client_id = getattr(settings, 'MELHOR_ENVIO_CLIENT_ID', None)
        client_secret = getattr(settings, 'MELHOR_ENVIO_CLIENT_SECRET', None)

        if client_id and client_secret:
            me = MelhorEnvioClient(
                client_id=client_id,
                client_secret=client_secret,
                sandbox=True
            )
            cotacoes = await me.calcular_frete(
                cep_origem=cep_origem,
                cep_destino=cep_destino,
                peso=peso,
                altura=altura,
                largura=largura,
                comprimento=comprimento
            )
            resultados["melhor_envio"] = {
                "total_cotacoes": len(cotacoes),
                "cotacoes": cotacoes
            }
    except Exception as e:
        logger.error(f"Erro ao calcular Melhor Envio: {str(e)}")
        resultados["erros"].append(f"Melhor Envio: {str(e)}")

    return resultados
