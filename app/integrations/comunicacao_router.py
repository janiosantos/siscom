"""
Router para integrações de Comunicação (Email e SMS)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr

from app.modules.auth.dependencies import get_current_user
from app.integrations.email import EmailClient, EmailProvider
from app.integrations.sms import SMSClient
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/comunicacao", tags=["Comunicação"])


# Schemas Email
class EnviarEmailRequest(BaseModel):
    """Schema para enviar email"""
    destinatario: EmailStr = Field(..., description="Email do destinatário")
    assunto: str = Field(..., min_length=1, description="Assunto do email")
    corpo_html: str = Field(..., min_length=1, description="Corpo do email em HTML")
    corpo_texto: Optional[str] = Field(None, description="Corpo do email em texto puro")
    reply_to: Optional[EmailStr] = Field(None, description="Email para resposta")
    cc: Optional[List[EmailStr]] = Field(None, description="Lista de emails em cópia")
    bcc: Optional[List[EmailStr]] = Field(None, description="Lista de emails em cópia oculta")


class EnviarTemplateRequest(BaseModel):
    """Schema para enviar email com template"""
    destinatario: EmailStr = Field(..., description="Email do destinatário")
    template_id: str = Field(..., description="ID do template no SendGrid")
    dados_template: Dict[str, Any] = Field(..., description="Dados dinâmicos do template")


# Schemas SMS
class EnviarSMSRequest(BaseModel):
    """Schema para enviar SMS"""
    destinatario: str = Field(..., description="Número do destinatário (+5511999999999)")
    mensagem: str = Field(..., min_length=1, max_length=1600, description="Texto da mensagem")


class EnviarWhatsAppRequest(BaseModel):
    """Schema para enviar WhatsApp"""
    destinatario: str = Field(..., description="Número do destinatário (+5511999999999)")
    mensagem: str = Field(..., min_length=1, description="Texto da mensagem")
    media_url: Optional[str] = Field(None, description="URL de mídia (imagem, vídeo)")


# Helper para obter client de email
def get_email_client() -> EmailClient:
    """Retorna client de email configurado"""
    # Tentar SendGrid primeiro
    sendgrid_key = getattr(settings, 'SENDGRID_API_KEY', None)
    if sendgrid_key:
        sender_email = getattr(settings, 'SENDER_EMAIL', 'noreply@siscom.com')
        sender_name = getattr(settings, 'SENDER_NAME', 'SISCOM')
        return EmailClient(
            provider=EmailProvider.SENDGRID,
            api_key=sendgrid_key,
            sender_email=sender_email,
            sender_name=sender_name
        )

    # Fallback para AWS SES
    aws_key = getattr(settings, 'AWS_SES_ACCESS_KEY', None)
    if aws_key:
        sender_email = getattr(settings, 'SENDER_EMAIL', 'noreply@siscom.com')
        sender_name = getattr(settings, 'SENDER_NAME', 'SISCOM')
        return EmailClient(
            provider=EmailProvider.AWS_SES,
            api_key=aws_key,
            sender_email=sender_email,
            sender_name=sender_name
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Nenhum provedor de email configurado (SendGrid ou AWS SES)"
    )


# Helper para obter client de SMS
def get_sms_client() -> SMSClient:
    """Retorna client de SMS configurado"""
    account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

    if not account_sid or not auth_token or not phone_number:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Credenciais do Twilio não configuradas"
        )

    return SMSClient(
        account_sid=account_sid,
        auth_token=auth_token,
        phone_number=phone_number
    )


# Endpoints Email
@router.post("/email/enviar")
async def enviar_email(
    dados: EnviarEmailRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia um email

    Suporta SendGrid e AWS SES. Usa o provedor configurado no .env.
    """
    logger.info(f"Enviando email para {dados.destinatario} - Usuário: {current_user.id}")

    try:
        client = get_email_client()

        resultado = await client.enviar_email(
            destinatario=dados.destinatario,
            assunto=dados.assunto,
            corpo_html=dados.corpo_html,
            corpo_texto=dados.corpo_texto,
            reply_to=dados.reply_to,
            cc=dados.cc,
            bcc=dados.bcc
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar email: {str(e)}"
        )


@router.post("/email/template")
async def enviar_email_template(
    dados: EnviarTemplateRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia email usando template do SendGrid

    Requer SendGrid configurado. Templates devem ser criados no painel do SendGrid.
    """
    logger.info(f"Enviando email template '{dados.template_id}' para {dados.destinatario}")

    try:
        client = get_email_client()

        if client.provider != EmailProvider.SENDGRID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Templates são suportados apenas no SendGrid"
            )

        resultado = await client.enviar_template(
            destinatario=dados.destinatario,
            template_id=dados.template_id,
            dados_template=dados.dados_template
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar template: {str(e)}"
        )


# Endpoints SMS
@router.post("/sms/enviar")
async def enviar_sms(
    dados: EnviarSMSRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia um SMS via Twilio

    Número deve estar no formato internacional: +5511999999999
    """
    logger.info(f"Enviando SMS para {dados.destinatario} - Usuário: {current_user.id}")

    try:
        client = get_sms_client()

        resultado = await client.enviar_sms(
            destinatario=dados.destinatario,
            mensagem=dados.mensagem
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar SMS: {str(e)}"
        )


@router.get("/sms/consultar/{message_sid}")
async def consultar_sms(
    message_sid: str,
    current_user=Depends(get_current_user)
):
    """
    Consulta status de um SMS enviado

    Retorna informações detalhadas sobre o status da mensagem.
    """
    logger.info(f"Consultando SMS: {message_sid}")

    try:
        client = get_sms_client()

        resultado = await client.consultar_mensagem(message_sid)

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao consultar SMS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao consultar SMS: {str(e)}"
        )


# Endpoints WhatsApp
@router.post("/whatsapp/enviar")
async def enviar_whatsapp(
    dados: EnviarWhatsAppRequest,
    current_user=Depends(get_current_user)
):
    """
    Envia mensagem via WhatsApp Business (Twilio)

    Requer WhatsApp Business configurado no Twilio.
    Número deve estar no formato: +5511999999999
    """
    logger.info(f"Enviando WhatsApp para {dados.destinatario} - Usuário: {current_user.id}")

    try:
        client = get_sms_client()

        resultado = await client.enviar_whatsapp(
            destinatario=dados.destinatario,
            mensagem=dados.mensagem,
            media_url=dados.media_url
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao enviar WhatsApp: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao enviar WhatsApp: {str(e)}"
        )


@router.get("/numero/verificar/{numero}")
async def verificar_numero(
    numero: str,
    current_user=Depends(get_current_user)
):
    """
    Verifica se um número é válido (Twilio Lookup API)

    Retorna informações sobre o número (operadora, tipo, país).
    Número deve estar no formato: +5511999999999
    """
    logger.info(f"Verificando número: {numero}")

    try:
        client = get_sms_client()

        resultado = await client.verificar_numero(numero)

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar número: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao verificar número: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Verifica se as integrações de comunicação estão configuradas

    Retorna status de cada provedor (SendGrid, AWS SES, Twilio).
    """
    status_config = {
        "sendgrid": bool(getattr(settings, 'SENDGRID_API_KEY', None)),
        "aws_ses": bool(getattr(settings, 'AWS_SES_ACCESS_KEY', None)),
        "twilio": bool(
            getattr(settings, 'TWILIO_ACCOUNT_SID', None) and
            getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        )
    }

    return {
        "status": "ok" if any(status_config.values()) else "sem_configuracao",
        "provedores": status_config,
        "email_ativo": status_config["sendgrid"] or status_config["aws_ses"],
        "sms_ativo": status_config["twilio"]
    }
