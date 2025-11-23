"""
Serviço para gerenciamento de Certificados Digitais A1 e A3
Utilizado para assinatura de NF-e, NFC-e e comunicação com SEFAZ
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import base64

logger = logging.getLogger(__name__)


class CertificadoDigital:
    """Representa um certificado digital A1 ou A3"""

    def __init__(
        self,
        tipo: str,  # A1 ou A3
        arquivo_pfx: Optional[bytes] = None,
        senha: str = "",
        caminho_certificado: Optional[str] = None
    ):
        self.tipo = tipo
        self.arquivo_pfx = arquivo_pfx
        self.senha = senha
        self.caminho_certificado = caminho_certificado
        self._certificado = None
        self._chave_privada = None
        self._valido_ate: Optional[datetime] = None

    def carregar(self):
        """
        Carrega o certificado digital

        Para A1: carrega do arquivo .pfx
        Para A3: conecta ao token/smartcard
        """
        try:
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend
            from cryptography import x509

            if self.tipo == "A1":
                # Carregar certificado A1 do arquivo PFX
                if self.arquivo_pfx:
                    pfx_data = self.arquivo_pfx
                elif self.caminho_certificado:
                    with open(self.caminho_certificado, 'rb') as f:
                        pfx_data = f.read()
                else:
                    raise ValueError("Arquivo PFX não fornecido")

                # Importar PFX (PKCS12)
                from cryptography.hazmat.primitives.serialization import pkcs12

                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                    pfx_data,
                    self.senha.encode() if self.senha else None,
                    default_backend()
                )

                self._chave_privada = private_key
                self._certificado = certificate
                self._valido_ate = certificate.not_valid_after

                logger.info(
                    f"Certificado A1 carregado com sucesso - "
                    f"Válido até: {self._valido_ate}"
                )

            elif self.tipo == "A3":
                # Para A3, seria necessário integração com PKCS#11
                # Aqui está um placeholder para implementação futura
                logger.warning(
                    "Certificado A3 requer biblioteca PKCS#11 - "
                    "Implementação simplificada"
                )
                # TODO: Implementar com python-pkcs11
                raise NotImplementedError(
                    "Suporte a certificado A3 requer biblioteca PKCS#11"
                )

        except Exception as e:
            logger.error(f"Erro ao carregar certificado: {str(e)}")
            raise

    @property
    def valido(self) -> bool:
        """Verifica se o certificado está válido"""
        if not self._valido_ate:
            return False
        return datetime.now() < self._valido_ate

    @property
    def dias_para_vencer(self) -> int:
        """Retorna quantos dias faltam para o certificado vencer"""
        if not self._valido_ate:
            return 0
        delta = self._valido_ate - datetime.now()
        return max(0, delta.days)

    def assinar_xml(self, xml_content: str) -> str:
        """
        Assina um documento XML (NF-e, NFC-e, etc)

        Args:
            xml_content: Conteúdo XML a ser assinado

        Returns:
            XML assinado
        """
        if not self._chave_privada or not self._certificado:
            raise ValueError("Certificado não carregado")

        try:
            from lxml import etree
            from signxml import XMLSigner

            # Parse XML
            root = etree.fromstring(xml_content.encode())

            # Assinar XML usando XMLSigner
            signer = XMLSigner(
                method=XMLSigner.SignatureMethod.RSA_SHA1,
                digest_algorithm='sha1',
                c14n_algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315'
            )

            signed_root = signer.sign(
                root,
                key=self._chave_privada,
                cert=self._certificado
            )

            # Converter de volta para string
            xml_assinado = etree.tostring(
                signed_root,
                encoding='unicode',
                pretty_print=True
            )

            logger.info("XML assinado com sucesso")
            return xml_assinado

        except Exception as e:
            logger.error(f"Erro ao assinar XML: {str(e)}")
            raise

    def obter_informacoes(self) -> Dict[str, Any]:
        """Retorna informações sobre o certificado"""
        if not self._certificado:
            return {}

        from cryptography import x509

        subject = self._certificado.subject
        issuer = self._certificado.issuer

        return {
            "tipo": self.tipo,
            "subject": {
                "CN": subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value,
                "O": subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME)[0].value if subject.get_attributes_for_oid(x509.oid.NameOID.ORGANIZATION_NAME) else None,
            },
            "issuer": {
                "CN": issuer.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value,
            },
            "valido_de": self._certificado.not_valid_before.isoformat(),
            "valido_ate": self._certificado.not_valid_after.isoformat(),
            "dias_para_vencer": self.dias_para_vencer,
            "valido": self.valido
        }


class CertificadoService:
    """Serviço para gerenciamento de certificados digitais"""

    def __init__(self):
        self._certificados: Dict[str, CertificadoDigital] = {}

    def adicionar_certificado_a1(
        self,
        empresa_id: int,
        arquivo_pfx: bytes,
        senha: str
    ) -> Dict[str, Any]:
        """
        Adiciona e carrega um certificado A1

        Args:
            empresa_id: ID da empresa
            arquivo_pfx: Conteúdo do arquivo .pfx
            senha: Senha do certificado

        Returns:
            Informações do certificado carregado
        """
        logger.info(f"Adicionando certificado A1 para empresa {empresa_id}")

        certificado = CertificadoDigital(
            tipo="A1",
            arquivo_pfx=arquivo_pfx,
            senha=senha
        )

        certificado.carregar()

        # Verificar validade
        if not certificado.valido:
            raise ValueError("Certificado vencido ou inválido")

        # Alertar se está próximo do vencimento (30 dias)
        if certificado.dias_para_vencer <= 30:
            logger.warning(
                f"Certificado vence em {certificado.dias_para_vencer} dias!"
            )

        # Armazenar certificado
        chave = f"empresa_{empresa_id}"
        self._certificados[chave] = certificado

        logger.info(f"Certificado A1 adicionado com sucesso - Empresa {empresa_id}")

        return certificado.obter_informacoes()

    def adicionar_certificado_a3(
        self,
        empresa_id: int,
        pin: str,
        slot: int = 0
    ) -> Dict[str, Any]:
        """
        Adiciona e conecta a um certificado A3 (token/smartcard)

        Args:
            empresa_id: ID da empresa
            pin: PIN do token/smartcard
            slot: Slot do token (padrão: 0)

        Returns:
            Informações do certificado
        """
        logger.info(f"Conectando ao certificado A3 para empresa {empresa_id}")

        # Implementação simplificada - requer PKCS#11
        raise NotImplementedError(
            "Suporte a certificado A3 requer biblioteca PKCS#11. "
            "Instale: pip install python-pkcs11"
        )

    def obter_certificado(self, empresa_id: int) -> Optional[CertificadoDigital]:
        """Retorna o certificado de uma empresa"""
        chave = f"empresa_{empresa_id}"
        return self._certificados.get(chave)

    def assinar_xml_empresa(
        self,
        empresa_id: int,
        xml_content: str
    ) -> str:
        """
        Assina um XML usando o certificado da empresa

        Args:
            empresa_id: ID da empresa
            xml_content: Conteúdo XML

        Returns:
            XML assinado
        """
        certificado = self.obter_certificado(empresa_id)

        if not certificado:
            raise ValueError(f"Certificado não encontrado para empresa {empresa_id}")

        if not certificado.valido:
            raise ValueError("Certificado vencido ou inválido")

        return certificado.assinar_xml(xml_content)

    def verificar_validade_certificados(self) -> Dict[str, Any]:
        """
        Verifica a validade de todos os certificados cadastrados

        Returns:
            Relatório de validade
        """
        relatorio = {
            "total": len(self._certificados),
            "validos": 0,
            "vencidos": 0,
            "proximo_vencimento": [],
            "detalhes": []
        }

        for chave, certificado in self._certificados.items():
            empresa_id = chave.replace("empresa_", "")

            info = {
                "empresa_id": empresa_id,
                "tipo": certificado.tipo,
                "valido": certificado.valido,
                "dias_para_vencer": certificado.dias_para_vencer
            }

            if certificado.valido:
                relatorio["validos"] += 1

                # Alerta se vence em 30 dias ou menos
                if certificado.dias_para_vencer <= 30:
                    relatorio["proximo_vencimento"].append(info)
            else:
                relatorio["vencidos"] += 1

            relatorio["detalhes"].append(info)

        logger.info(
            f"Verificação de certificados - "
            f"Total: {relatorio['total']}, "
            f"Válidos: {relatorio['validos']}, "
            f"Vencidos: {relatorio['vencidos']}"
        )

        return relatorio

    def remover_certificado(self, empresa_id: int):
        """Remove o certificado de uma empresa"""
        chave = f"empresa_{empresa_id}"
        if chave in self._certificados:
            del self._certificados[chave]
            logger.info(f"Certificado removido - Empresa {empresa_id}")
        else:
            logger.warning(f"Certificado não encontrado para remoção - Empresa {empresa_id}")


# Instância global do serviço
certificado_service = CertificadoService()
