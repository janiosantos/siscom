"""
Serviço para geração e envio de NF-e (Nota Fiscal Eletrônica) e NFC-e
Integração com SEFAZ (Secretaria da Fazenda)
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from lxml import etree
import hashlib

logger = logging.getLogger(__name__)


class NFe:
    """Representa uma NF-e (Nota Fiscal Eletrônica)"""

    def __init__(
        self,
        numero: int,
        serie: int,
        tipo: str,  # "NFe" ou "NFCe"
        emitente: Dict[str, Any],
        destinatario: Dict[str, Any],
        itens: List[Dict[str, Any]],
        natureza_operacao: str = "Venda de mercadoria"
    ):
        self.numero = numero
        self.serie = serie
        self.tipo = tipo
        self.emitente = emitente
        self.destinatario = destinatario
        self.itens = itens
        self.natureza_operacao = natureza_operacao
        self.chave_acesso: Optional[str] = None
        self.protocolo_autorizacao: Optional[str] = None
        self.data_emissao = datetime.now()

    def gerar_xml(self) -> str:
        """
        Gera o XML da NF-e no formato SEFAZ

        Returns:
            XML da NF-e
        """
        # Namespace NFe
        ns = "http://www.portalfiscal.inf.br/nfe"
        nsmap = {None: ns}

        # Root
        nfe = etree.Element("{%s}NFe" % ns, nsmap=nsmap, xmlns=ns)

        # infNFe
        inf_nfe = etree.SubElement(nfe, "infNFe", versao="4.00")

        # Gerar chave de acesso
        self.chave_acesso = self._gerar_chave_acesso()
        inf_nfe.set("Id", f"NFe{self.chave_acesso}")

        # ide - Identificação
        ide = self._gerar_ide(inf_nfe)

        # emit - Emitente
        emit = self._gerar_emitente(inf_nfe)

        # dest - Destinatário
        if self.destinatario.get("cnpj_cpf"):  # NFC-e pode não ter destinatário
            dest = self._gerar_destinatario(inf_nfe)

        # det - Itens/Produtos
        for idx, item in enumerate(self.itens, start=1):
            det = self._gerar_item(inf_nfe, item, idx)

        # total - Totais da NF-e
        total = self._gerar_totais(inf_nfe)

        # transp - Transporte
        transp = etree.SubElement(inf_nfe, "transp")
        mod_frete = etree.SubElement(transp, "modFrete")
        mod_frete.text = "9"  # Sem frete

        # pag - Pagamento
        pag = self._gerar_pagamento(inf_nfe)

        # infAdic - Informações Adicionais
        if self.tipo == "NFCe":
            inf_adic = etree.SubElement(inf_nfe, "infAdic")
            inf_cpl = etree.SubElement(inf_adic, "infCpl")
            inf_cpl.text = "Documento emitido por ME ou EPP optante pelo Simples Nacional"

        # Converter para string
        xml_str = etree.tostring(
            nfe,
            encoding='unicode',
            pretty_print=True,
            xml_declaration=True
        )

        return xml_str

    def _gerar_chave_acesso(self) -> str:
        """
        Gera a chave de acesso de 44 dígitos

        Formato: UF + AAMM + CNPJ + Modelo + Serie + Numero + Forma Emissão + Código + DV
        """
        # UF (2 dígitos)
        uf_codigo = self.emitente.get("uf_codigo", "35")  # 35 = SP

        # AAMM (4 dígitos - Ano e Mês)
        aamm = self.data_emissao.strftime("%y%m")

        # CNPJ (14 dígitos)
        cnpj = self.emitente["cnpj"].replace(".", "").replace("/", "").replace("-", "").zfill(14)

        # Modelo (2 dígitos) - 55 = NFe, 65 = NFCe
        modelo = "65" if self.tipo == "NFCe" else "55"

        # Série (3 dígitos)
        serie = str(self.serie).zfill(3)

        # Número (9 dígitos)
        numero = str(self.numero).zfill(9)

        # Forma de Emissão (1 dígito) - 1 = Normal
        forma_emissao = "1"

        # Código Numérico (8 dígitos) - Gerado aleatoriamente
        codigo_numerico = hashlib.md5(
            f"{cnpj}{numero}{serie}".encode()
        ).hexdigest()[:8].upper()
        codigo_numerico = str(int(codigo_numerico, 16))[:8].zfill(8)

        # Montar chave sem DV
        chave_sem_dv = (
            uf_codigo + aamm + cnpj + modelo + serie +
            numero + forma_emissao + codigo_numerico
        )

        # Calcular DV (Dígito Verificador) - Módulo 11
        dv = self._calcular_dv_chave(chave_sem_dv)

        chave_completa = chave_sem_dv + str(dv)

        return chave_completa

    def _calcular_dv_chave(self, chave: str) -> int:
        """Calcula o dígito verificador da chave de acesso (Módulo 11)"""
        multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
        soma = 0
        idx_mult = 0

        for i in range(len(chave) - 1, -1, -1):
            soma += int(chave[i]) * multiplicadores[idx_mult]
            idx_mult = (idx_mult + 1) % 8

        resto = soma % 11
        dv = 0 if resto in [0, 1] else 11 - resto

        return dv

    def _gerar_ide(self, parent):
        """Gera tag ide (Identificação)"""
        ide = etree.SubElement(parent, "ide")

        # Código UF
        c_uf = etree.SubElement(ide, "cUF")
        c_uf.text = self.emitente.get("uf_codigo", "35")

        # Código Numérico
        c_nf = etree.SubElement(ide, "cNF")
        c_nf.text = self.chave_acesso[35:43]

        # Natureza da Operação
        nat_op = etree.SubElement(ide, "natOp")
        nat_op.text = self.natureza_operacao

        # Modelo
        mod = etree.SubElement(ide, "mod")
        mod.text = "65" if self.tipo == "NFCe" else "55"

        # Série
        serie = etree.SubElement(ide, "serie")
        serie.text = str(self.serie)

        # Número
        n_nf = etree.SubElement(ide, "nNF")
        n_nf.text = str(self.numero)

        # Data/Hora Emissão
        dh_emi = etree.SubElement(ide, "dhEmi")
        dh_emi.text = self.data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00")

        # Tipo NF-e (1 = Saída)
        tp_nf = etree.SubElement(ide, "tpNF")
        tp_nf.text = "1"

        # Identificação do Destino (1 = Operação interna)
        id_dest = etree.SubElement(ide, "idDest")
        id_dest.text = "1"

        # Código Município
        c_mun_fg = etree.SubElement(ide, "cMunFG")
        c_mun_fg.text = self.emitente.get("municipio_codigo", "3550308")  # São Paulo

        # Tipo de Impressão (4 = DANFE NFC-e, 1 = DANFE Retrato)
        tp_imp = etree.SubElement(ide, "tpImp")
        tp_imp.text = "4" if self.tipo == "NFCe" else "1"

        # Tipo de Emissão (1 = Normal)
        tp_emis = etree.SubElement(ide, "tpEmis")
        tp_emis.text = "1"

        # Dígito Verificador
        c_dv = etree.SubElement(ide, "cDV")
        c_dv.text = self.chave_acesso[-1]

        # Ambiente (2 = Homologação, 1 = Produção)
        tp_amb = etree.SubElement(ide, "tpAmb")
        tp_amb.text = "2"  # Homologação

        # Finalidade (1 = Normal)
        fin_nfe = etree.SubElement(ide, "finNFe")
        fin_nfe.text = "1"

        # Consumidor Final (1 = Sim)
        ind_final = etree.SubElement(ide, "indFinal")
        ind_final.text = "1"

        # Presença do comprador (1 = Operação presencial)
        ind_pres = etree.SubElement(ide, "indPres")
        ind_pres.text = "1"

        # Processo de emissão (0 = Aplicativo do contribuinte)
        proc_emi = etree.SubElement(ide, "procEmi")
        proc_emi.text = "0"

        # Versão do aplicativo
        ver_proc = etree.SubElement(ide, "verProc")
        ver_proc.text = "1.0"

        return ide

    def _gerar_emitente(self, parent):
        """Gera tag emit (Emitente)"""
        emit = etree.SubElement(parent, "emit")

        cnpj = etree.SubElement(emit, "CNPJ")
        cnpj.text = self.emitente["cnpj"].replace(".", "").replace("/", "").replace("-", "")

        x_nome = etree.SubElement(emit, "xNome")
        x_nome.text = self.emitente["razao_social"]

        x_fant = etree.SubElement(emit, "xFant")
        x_fant.text = self.emitente.get("nome_fantasia", self.emitente["razao_social"])

        # Endereço
        ender_emit = etree.SubElement(emit, "enderEmit")

        x_lgr = etree.SubElement(ender_emit, "xLgr")
        x_lgr.text = self.emitente["endereco"]

        nro = etree.SubElement(ender_emit, "nro")
        nro.text = self.emitente["numero"]

        x_bairro = etree.SubElement(ender_emit, "xBairro")
        x_bairro.text = self.emitente["bairro"]

        c_mun = etree.SubElement(ender_emit, "cMun")
        c_mun.text = self.emitente.get("municipio_codigo", "3550308")

        x_mun = etree.SubElement(ender_emit, "xMun")
        x_mun.text = self.emitente["municipio"]

        uf = etree.SubElement(ender_emit, "UF")
        uf.text = self.emitente["uf"]

        cep = etree.SubElement(ender_emit, "CEP")
        cep.text = self.emitente["cep"].replace("-", "")

        c_pais = etree.SubElement(ender_emit, "cPais")
        c_pais.text = "1058"  # Brasil

        x_pais = etree.SubElement(ender_emit, "xPais")
        x_pais.text = "BRASIL"

        # IE
        ie = etree.SubElement(emit, "IE")
        ie.text = self.emitente["inscricao_estadual"]

        # CRT - Código de Regime Tributário (1 = Simples Nacional)
        crt = etree.SubElement(emit, "CRT")
        crt.text = self.emitente.get("crt", "1")

        return emit

    def _gerar_destinatario(self, parent):
        """Gera tag dest (Destinatário)"""
        dest = etree.SubElement(parent, "dest")

        # CPF ou CNPJ
        doc = self.destinatario["cnpj_cpf"].replace(".", "").replace("/", "").replace("-", "")
        if len(doc) == 11:
            cpf = etree.SubElement(dest, "CPF")
            cpf.text = doc
        else:
            cnpj = etree.SubElement(dest, "CNPJ")
            cnpj.text = doc

        x_nome = etree.SubElement(dest, "xNome")
        x_nome.text = self.destinatario["nome"]

        # Endereço (simplificado para NFCe)
        if self.tipo == "NFe":
            ender_dest = etree.SubElement(dest, "enderDest")

            x_lgr = etree.SubElement(ender_dest, "xLgr")
            x_lgr.text = self.destinatario.get("endereco", "SEM ENDERECO")

            nro = etree.SubElement(ender_dest, "nro")
            nro.text = self.destinatario.get("numero", "SN")

            x_bairro = etree.SubElement(ender_dest, "xBairro")
            x_bairro.text = self.destinatario.get("bairro", "CENTRO")

            c_mun = etree.SubElement(ender_dest, "cMun")
            c_mun.text = self.destinatario.get("municipio_codigo", "3550308")

            x_mun = etree.SubElement(ender_dest, "xMun")
            x_mun.text = self.destinatario.get("municipio", "SAO PAULO")

            uf = etree.SubElement(ender_dest, "UF")
            uf.text = self.destinatario.get("uf", "SP")

            cep = etree.SubElement(ender_dest, "CEP")
            cep.text = self.destinatario.get("cep", "00000000").replace("-", "")

            c_pais = etree.SubElement(ender_dest, "cPais")
            c_pais.text = "1058"

            x_pais = etree.SubElement(ender_dest, "xPais")
            x_pais.text = "BRASIL"

        # Indicador IE (9 = Não Contribuinte)
        ind_ie_dest = etree.SubElement(dest, "indIEDest")
        ind_ie_dest.text = "9"

        return dest

    def _gerar_item(self, parent, item: Dict[str, Any], numero: int):
        """Gera tag det (Detalhe - Item)"""
        det = etree.SubElement(parent, "det", nItem=str(numero))

        # prod - Produto
        prod = etree.SubElement(det, "prod")

        c_prod = etree.SubElement(prod, "cProd")
        c_prod.text = str(item["codigo"])

        x_prod = etree.SubElement(prod, "xProd")
        x_prod.text = item["descricao"]

        ncm = etree.SubElement(prod, "NCM")
        ncm.text = item.get("ncm", "00000000")

        cfop = etree.SubElement(prod, "CFOP")
        cfop.text = item.get("cfop", "5102")

        u_com = etree.SubElement(prod, "uCom")
        u_com.text = item.get("unidade", "UN")

        q_com = etree.SubElement(prod, "qCom")
        q_com.text = f"{item['quantidade']:.4f}"

        v_un_com = etree.SubElement(prod, "vUnCom")
        v_un_com.text = f"{item['valor_unitario']:.2f}"

        v_prod = etree.SubElement(prod, "vProd")
        v_prod.text = f"{item['quantidade'] * item['valor_unitario']:.2f}"

        u_trib = etree.SubElement(prod, "uTrib")
        u_trib.text = item.get("unidade", "UN")

        q_trib = etree.SubElement(prod, "qTrib")
        q_trib.text = f"{item['quantidade']:.4f}"

        v_un_trib = etree.SubElement(prod, "vUnTrib")
        v_un_trib.text = f"{item['valor_unitario']:.2f}"

        ind_tot = etree.SubElement(prod, "indTot")
        ind_tot.text = "1"  # Compõe total da NF-e

        # imposto - Impostos (Simplificado - Simples Nacional)
        imposto = etree.SubElement(det, "imposto")

        icms = etree.SubElement(imposto, "ICMS")
        icms_sn102 = etree.SubElement(icms, "ICMSSN102")

        orig = etree.SubElement(icms_sn102, "orig")
        orig.text = "0"  # Nacional

        csosn = etree.SubElement(icms_sn102, "CSOSN")
        csosn.text = "102"  # Simples Nacional - sem permissão de crédito

        return det

    def _gerar_totais(self, parent):
        """Gera tag total (Totais)"""
        total = etree.SubElement(parent, "total")
        icms_tot = etree.SubElement(total, "ICMSTot")

        # Calcular totais
        v_bc = Decimal("0.00")
        v_icms = Decimal("0.00")
        v_bc_st = Decimal("0.00")
        v_st = Decimal("0.00")
        v_prod = sum(
            Decimal(str(item["quantidade"])) * Decimal(str(item["valor_unitario"]))
            for item in self.itens
        )
        v_frete = Decimal("0.00")
        v_seg = Decimal("0.00")
        v_desc = Decimal("0.00")
        v_ii = Decimal("0.00")
        v_ipi = Decimal("0.00")
        v_pis = Decimal("0.00")
        v_cofins = Decimal("0.00")
        v_outro = Decimal("0.00")
        v_nf = v_prod

        etree.SubElement(icms_tot, "vBC").text = f"{v_bc:.2f}"
        etree.SubElement(icms_tot, "vICMS").text = f"{v_icms:.2f}"
        etree.SubElement(icms_tot, "vICMSDeson").text = "0.00"
        etree.SubElement(icms_tot, "vFCP").text = "0.00"
        etree.SubElement(icms_tot, "vBCST").text = f"{v_bc_st:.2f}"
        etree.SubElement(icms_tot, "vST").text = f"{v_st:.2f}"
        etree.SubElement(icms_tot, "vFCPST").text = "0.00"
        etree.SubElement(icms_tot, "vFCPSTRet").text = "0.00"
        etree.SubElement(icms_tot, "vProd").text = f"{v_prod:.2f}"
        etree.SubElement(icms_tot, "vFrete").text = f"{v_frete:.2f}"
        etree.SubElement(icms_tot, "vSeg").text = f"{v_seg:.2f}"
        etree.SubElement(icms_tot, "vDesc").text = f"{v_desc:.2f}"
        etree.SubElement(icms_tot, "vII").text = f"{v_ii:.2f}"
        etree.SubElement(icms_tot, "vIPI").text = f"{v_ipi:.2f}"
        etree.SubElement(icms_tot, "vIPIDevol").text = "0.00"
        etree.SubElement(icms_tot, "vPIS").text = f"{v_pis:.2f}"
        etree.SubElement(icms_tot, "vCOFINS").text = f"{v_cofins:.2f}"
        etree.SubElement(icms_tot, "vOutro").text = f"{v_outro:.2f}"
        etree.SubElement(icms_tot, "vNF").text = f"{v_nf:.2f}"

        return total

    def _gerar_pagamento(self, parent):
        """Gera tag pag (Pagamento)"""
        pag = etree.SubElement(parent, "pag")
        det_pag = etree.SubElement(pag, "detPag")

        # Forma de pagamento (01 = Dinheiro)
        ind_pag = etree.SubElement(det_pag, "indPag")
        ind_pag.text = "0"  # Pagamento à vista

        t_pag = etree.SubElement(det_pag, "tPag")
        t_pag.text = "01"  # Dinheiro

        # Valor do pagamento
        v_pag = etree.SubElement(det_pag, "vPag")
        v_total = sum(
            Decimal(str(item["quantidade"])) * Decimal(str(item["valor_unitario"]))
            for item in self.itens
        )
        v_pag.text = f"{v_total:.2f}"

        return pag


class NFeService:
    """Serviço para gerenciamento de NF-e e NFC-e"""

    def __init__(self):
        self.ambiente = "homologacao"  # ou "producao"

    def criar_nfe(
        self,
        numero: int,
        serie: int,
        emitente: Dict[str, Any],
        destinatario: Dict[str, Any],
        itens: List[Dict[str, Any]],
        natureza_operacao: str = "Venda de mercadoria"
    ) -> NFe:
        """
        Cria uma NF-e

        Args:
            numero: Número da NF-e
            serie: Série da NF-e
            emitente: Dados do emitente
            destinatario: Dados do destinatário
            itens: Lista de itens/produtos
            natureza_operacao: Natureza da operação

        Returns:
            Objeto NFe
        """
        logger.info(f"Criando NF-e - Número: {numero}, Série: {serie}")

        nfe = NFe(
            numero=numero,
            serie=serie,
            tipo="NFe",
            emitente=emitente,
            destinatario=destinatario,
            itens=itens,
            natureza_operacao=natureza_operacao
        )

        return nfe

    def criar_nfce(
        self,
        numero: int,
        serie: int,
        emitente: Dict[str, Any],
        itens: List[Dict[str, Any]],
        destinatario: Optional[Dict[str, Any]] = None
    ) -> NFe:
        """
        Cria uma NFC-e (Nota Fiscal de Consumidor Eletrônica)

        Args:
            numero: Número da NFC-e
            serie: Série da NFC-e
            emitente: Dados do emitente
            itens: Lista de itens/produtos
            destinatario: Dados do destinatário (opcional para NFC-e)

        Returns:
            Objeto NFe
        """
        logger.info(f"Criando NFC-e - Número: {numero}, Série: {serie}")

        nfce = NFe(
            numero=numero,
            serie=serie,
            tipo="NFCe",
            emitente=emitente,
            destinatario=destinatario or {},
            itens=itens,
            natureza_operacao="Venda ao consumidor"
        )

        return nfce

    def enviar_para_sefaz(
        self,
        nfe: NFe,
        certificado_service,
        empresa_id: int
    ) -> Dict[str, Any]:
        """
        Envia NF-e/NFC-e para autorização da SEFAZ

        Args:
            nfe: Objeto NFe
            certificado_service: Serviço de certificado digital
            empresa_id: ID da empresa

        Returns:
            Resultado do envio
        """
        logger.info(f"Enviando {nfe.tipo} para SEFAZ - Chave: {nfe.chave_acesso}")

        # Gerar XML
        xml = nfe.gerar_xml()

        # Assinar XML
        xml_assinado = certificado_service.assinar_xml_empresa(empresa_id, xml)

        # TODO: Enviar para SEFAZ via Web Service
        # Aqui seria a integração com SOAP/REST da SEFAZ
        # Por ora, retornar simulação de sucesso

        logger.info(f"{nfe.tipo} enviada com sucesso (SIMULAÇÃO)")

        return {
            "sucesso": True,
            "chave_acesso": nfe.chave_acesso,
            "protocolo": "999999999999999",  # Simulado
            "data_autorizacao": datetime.now().isoformat(),
            "xml_assinado": xml_assinado,
            "mensagem": "NF-e autorizada (AMBIENTE DE HOMOLOGAÇÃO)"
        }

    def consultar_status_sefaz(self, uf: str) -> Dict[str, Any]:
        """
        Consulta status do serviço da SEFAZ

        Args:
            uf: Sigla da UF

        Returns:
            Status do serviço
        """
        # TODO: Implementar consulta real ao Web Service da SEFAZ
        logger.info(f"Consultando status SEFAZ - UF: {uf}")

        return {
            "uf": uf,
            "status": "online",
            "mensagem": "Serviço em operação",
            "data_consulta": datetime.now().isoformat()
        }

    def cancelar_nfe(
        self,
        chave_acesso: str,
        protocolo: str,
        justificativa: str,
        certificado_service,
        empresa_id: int
    ) -> Dict[str, Any]:
        """
        Cancela uma NF-e autorizada

        Args:
            chave_acesso: Chave de acesso da NF-e
            protocolo: Protocolo de autorização
            justificativa: Justificativa do cancelamento (min 15 caracteres)
            certificado_service: Serviço de certificado
            empresa_id: ID da empresa

        Returns:
            Resultado do cancelamento
        """
        if len(justificativa) < 15:
            raise ValueError("Justificativa deve ter no mínimo 15 caracteres")

        logger.info(f"Cancelando NF-e - Chave: {chave_acesso}")

        # TODO: Gerar XML de cancelamento e enviar para SEFAZ

        logger.info(f"NF-e cancelada com sucesso (SIMULAÇÃO)")

        return {
            "sucesso": True,
            "chave_acesso": chave_acesso,
            "protocolo_cancelamento": "999999999999998",  # Simulado
            "data_cancelamento": datetime.now().isoformat(),
            "mensagem": "Cancelamento homologado"
        }


# Instância global do serviço
nfe_service = NFeService()
