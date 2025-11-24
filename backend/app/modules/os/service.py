"""
Service Layer para Ordens de Serviço
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.os.repository import (
    TipoServicoRepository,
    TecnicoRepository,
    OrdemServicoRepository,
)
from app.modules.os.models import StatusOS
from app.modules.os.schemas import (
    TipoServicoCreate,
    TipoServicoUpdate,
    TipoServicoResponse,
    TipoServicoList,
    TecnicoCreate,
    TecnicoUpdate,
    TecnicoResponse,
    TecnicoList,
    OrdemServicoCreate,
    OrdemServicoUpdate,
    OrdemServicoResponse,
    OrdemServicoList,
    ItemOSCreate,
    ItemOSResponse,
    ApontamentoHorasCreate,
    ApontamentoHorasResponse,
    StatusOSEnum,
    FinalizarOSRequest,
    FaturarOSRequest,
)
from app.modules.produtos.repository import ProdutoRepository
from app.modules.clientes.repository import ClienteRepository
from app.modules.estoque.service import EstoqueService
from app.modules.estoque.schemas import SaidaEstoqueCreate
from app.modules.vendas.service import VendasService
from app.modules.vendas.schemas import VendaCreate, ItemVendaCreate
from app.modules.financeiro.service import FinanceiroService
from app.modules.financeiro.schemas import ContaReceberCreate
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
)


class OSService:
    """Service para regras de negócio de Ordens de Serviço"""

    def __init__(self, session: AsyncSession):
        self.tipo_servico_repo = TipoServicoRepository(session)
        self.tecnico_repo = TecnicoRepository(session)
        self.os_repo = OrdemServicoRepository(session)
        self.produto_repo = ProdutoRepository(session)
        self.cliente_repo = ClienteRepository(session)
        self.estoque_service = EstoqueService(session)
        self.session = session

    # ====================================
    # TIPO SERVIÇO
    # ====================================

    async def criar_tipo_servico(
        self, tipo_data: TipoServicoCreate
    ) -> TipoServicoResponse:
        """Cria novo tipo de serviço"""
        tipo = await self.tipo_servico_repo.create(tipo_data)
        return TipoServicoResponse.model_validate(tipo)

    async def get_tipo_servico(self, tipo_id: int) -> TipoServicoResponse:
        """Busca tipo de serviço por ID"""
        tipo = await self.tipo_servico_repo.get_by_id(tipo_id)
        if not tipo:
            raise NotFoundException(f"Tipo de serviço {tipo_id} não encontrado")
        return TipoServicoResponse.model_validate(tipo)

    async def list_tipos_servico(
        self, page: int = 1, page_size: int = 50, ativo: Optional[bool] = None
    ) -> TipoServicoList:
        """Lista tipos de serviço com paginação"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        tipos = await self.tipo_servico_repo.get_all(skip=skip, limit=page_size, ativo=ativo)
        total = await self.tipo_servico_repo.count(ativo=ativo)
        pages = math.ceil(total / page_size) if total > 0 else 1

        return TipoServicoList(
            items=[TipoServicoResponse.model_validate(t) for t in tipos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_tipo_servico(
        self, tipo_id: int, tipo_data: TipoServicoUpdate
    ) -> TipoServicoResponse:
        """Atualiza tipo de serviço"""
        tipo = await self.tipo_servico_repo.update(tipo_id, tipo_data)
        if not tipo:
            raise NotFoundException(f"Tipo de serviço {tipo_id} não encontrado")
        return TipoServicoResponse.model_validate(tipo)

    # ====================================
    # TÉCNICO
    # ====================================

    async def criar_tecnico(self, tecnico_data: TecnicoCreate) -> TecnicoResponse:
        """Cria novo técnico"""
        # Valida se CPF já existe
        tecnico_existente = await self.tecnico_repo.get_by_cpf(tecnico_data.cpf)
        if tecnico_existente:
            raise ValidationException(f"Já existe técnico com CPF {tecnico_data.cpf}")

        tecnico = await self.tecnico_repo.create(tecnico_data)
        return TecnicoResponse.model_validate(tecnico)

    async def get_tecnico(self, tecnico_id: int) -> TecnicoResponse:
        """Busca técnico por ID"""
        tecnico = await self.tecnico_repo.get_by_id(tecnico_id)
        if not tecnico:
            raise NotFoundException(f"Técnico {tecnico_id} não encontrado")
        return TecnicoResponse.model_validate(tecnico)

    async def list_tecnicos(
        self, page: int = 1, page_size: int = 50, ativo: Optional[bool] = None
    ) -> TecnicoList:
        """Lista técnicos com paginação"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        tecnicos = await self.tecnico_repo.get_all(skip=skip, limit=page_size, ativo=ativo)
        total = await self.tecnico_repo.count(ativo=ativo)
        pages = math.ceil(total / page_size) if total > 0 else 1

        return TecnicoList(
            items=[TecnicoResponse.model_validate(t) for t in tecnicos],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_tecnico(
        self, tecnico_id: int, tecnico_data: TecnicoUpdate
    ) -> TecnicoResponse:
        """Atualiza técnico"""
        # Se está atualizando CPF, valida se já existe
        if tecnico_data.cpf:
            tecnico_existente = await self.tecnico_repo.get_by_cpf(tecnico_data.cpf)
            if tecnico_existente and tecnico_existente.id != tecnico_id:
                raise ValidationException(f"Já existe técnico com CPF {tecnico_data.cpf}")

        tecnico = await self.tecnico_repo.update(tecnico_id, tecnico_data)
        if not tecnico:
            raise NotFoundException(f"Técnico {tecnico_id} não encontrado")
        return TecnicoResponse.model_validate(tecnico)

    # ====================================
    # ORDEM DE SERVIÇO
    # ====================================

    async def abrir_os(self, os_data: OrdemServicoCreate) -> OrdemServicoResponse:
        """
        Abre uma nova ordem de serviço

        Valida:
        - Cliente existe
        - Técnico existe e está ativo
        - Tipo de serviço existe e está ativo
        - Se produto_id informado, valida que existe e controla_serie
        - Se numero_serie informado, valida que produto controla_serie
        """
        # Valida cliente
        cliente = await self.cliente_repo.get_by_id(os_data.cliente_id)
        if not cliente:
            raise NotFoundException(f"Cliente {os_data.cliente_id} não encontrado")
        if not cliente.ativo:
            raise ValidationException(f"Cliente '{cliente.nome}' está inativo")

        # Valida técnico
        tecnico = await self.tecnico_repo.get_by_id(os_data.tecnico_id)
        if not tecnico:
            raise NotFoundException(f"Técnico {os_data.tecnico_id} não encontrado")
        if not tecnico.ativo:
            raise ValidationException(f"Técnico '{tecnico.nome}' está inativo")

        # Valida tipo de serviço
        tipo_servico = await self.tipo_servico_repo.get_by_id(os_data.tipo_servico_id)
        if not tipo_servico:
            raise NotFoundException(
                f"Tipo de serviço {os_data.tipo_servico_id} não encontrado"
            )
        if not tipo_servico.ativo:
            raise ValidationException(f"Tipo de serviço '{tipo_servico.nome}' está inativo")

        # Se produto informado (equipamento), valida
        if os_data.produto_id:
            produto = await self.produto_repo.get_by_id(os_data.produto_id)
            if not produto:
                raise NotFoundException(f"Produto {os_data.produto_id} não encontrado")
            if not produto.ativo:
                raise ValidationException(f"Produto '{produto.descricao}' está inativo")

            # Se número de série informado, valida que produto controla série
            if os_data.numero_serie:
                if not produto.controla_serie:
                    raise ValidationException(
                        f"Produto '{produto.descricao}' não controla número de série"
                    )

        # Se número de série informado mas produto não, erro
        if os_data.numero_serie and not os_data.produto_id:
            raise ValidationException(
                "Número de série informado mas produto (equipamento) não especificado"
            )

        # Define valor de mão de obra padrão se não informado
        if os_data.valor_mao_obra == 0:
            os_data.valor_mao_obra = float(tipo_servico.preco_padrao)

        # Cria OS
        os = await self.os_repo.create_os(os_data)
        await self.session.flush()
        await self.session.refresh(os)

        return OrdemServicoResponse.model_validate(os)

    async def get_os(self, os_id: int) -> OrdemServicoResponse:
        """Busca OS completa por ID"""
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")
        return OrdemServicoResponse.model_validate(os)

    async def list_os(
        self,
        page: int = 1,
        page_size: int = 50,
        cliente_id: Optional[int] = None,
        tecnico_id: Optional[int] = None,
        status: Optional[StatusOSEnum] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
    ) -> OrdemServicoList:
        """Lista ordens de serviço com filtros"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Converte enum se fornecido
        status_db = None
        if status:
            status_db = StatusOS(status.value)

        ordens = await self.os_repo.get_all(
            skip=skip,
            limit=page_size,
            cliente_id=cliente_id,
            tecnico_id=tecnico_id,
            status=status_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.os_repo.count(
            cliente_id=cliente_id,
            tecnico_id=tecnico_id,
            status=status_db,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrdemServicoList(
            items=[OrdemServicoResponse.model_validate(o) for o in ordens],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def atualizar_os(
        self, os_id: int, os_data: OrdemServicoUpdate
    ) -> OrdemServicoResponse:
        """Atualiza ordem de serviço"""
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        # Não permite atualizar OS concluída, cancelada ou faturada
        if os.status in [StatusOS.CONCLUIDA, StatusOS.CANCELADA, StatusOS.FATURADA]:
            raise BusinessRuleException(
                f"Não é possível atualizar OS com status '{os.status.value}'"
            )

        # Se está mudando técnico, valida
        if os_data.tecnico_id:
            tecnico = await self.tecnico_repo.get_by_id(os_data.tecnico_id)
            if not tecnico:
                raise NotFoundException(f"Técnico {os_data.tecnico_id} não encontrado")
            if not tecnico.ativo:
                raise ValidationException(f"Técnico '{tecnico.nome}' está inativo")

        os_atualizada = await self.os_repo.update(os_id, os_data)
        await self.session.flush()
        await self.session.refresh(os_atualizada)

        return OrdemServicoResponse.model_validate(os_atualizada)

    async def atribuir_tecnico(self, os_id: int, tecnico_id: int) -> OrdemServicoResponse:
        """Atribui ou reatribui técnico a uma OS"""
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        # Não permite atribuir técnico a OS concluída, cancelada ou faturada
        if os.status in [StatusOS.CONCLUIDA, StatusOS.CANCELADA, StatusOS.FATURADA]:
            raise BusinessRuleException(
                f"Não é possível atribuir técnico a OS com status '{os.status.value}'"
            )

        # Valida técnico
        tecnico = await self.tecnico_repo.get_by_id(tecnico_id)
        if not tecnico:
            raise NotFoundException(f"Técnico {tecnico_id} não encontrado")
        if not tecnico.ativo:
            raise ValidationException(f"Técnico '{tecnico.nome}' está inativo")

        os.tecnico_id = tecnico_id
        await self.session.flush()
        await self.session.refresh(os)

        return OrdemServicoResponse.model_validate(os)

    async def iniciar_os(self, os_id: int) -> OrdemServicoResponse:
        """Inicia uma OS (muda status para EM_ANDAMENTO)"""
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status != StatusOS.ABERTA:
            raise BusinessRuleException(
                f"Somente OS com status ABERTA pode ser iniciada. Status atual: {os.status.value}"
            )

        os_atualizada = await self.os_repo.atualizar_status(os_id, StatusOS.EM_ANDAMENTO)
        await self.session.flush()
        await self.session.refresh(os_atualizada)

        return OrdemServicoResponse.model_validate(os_atualizada)

    async def adicionar_material_os(
        self, os_id: int, material_data: ItemOSCreate
    ) -> ItemOSResponse:
        """
        Adiciona material (item) à OS e dá baixa automática no estoque

        Regras:
        - OS deve existir e não estar cancelada
        - Produto deve existir e estar ativo
        - Dá baixa automática no estoque via EstoqueService
        - Recalcula valor total da OS
        """
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status == StatusOS.CANCELADA:
            raise BusinessRuleException("Não é possível adicionar material a OS cancelada")

        # Valida produto
        produto = await self.produto_repo.get_by_id(material_data.produto_id)
        if not produto:
            raise NotFoundException(f"Produto {material_data.produto_id} não encontrado")
        if not produto.ativo:
            raise ValidationException(f"Produto '{produto.descricao}' está inativo")

        # Valida estoque disponível
        await self.estoque_service.validar_estoque_suficiente(
            material_data.produto_id, material_data.quantidade
        )

        # Adiciona item à OS
        item = await self.os_repo.create_item_os(os_id, material_data)

        # Dá baixa no estoque
        saida_data = SaidaEstoqueCreate(
            produto_id=material_data.produto_id,
            quantidade=material_data.quantidade,
            custo_unitario=material_data.preco_unitario,
            documento_referencia=f"OS-{os_id}",
            observacao=f"Material usado na OS #{os_id}",
            usuario_id=os.tecnico_id,  # Usa técnico como responsável
        )
        await self.estoque_service.saida_estoque(saida_data)

        # Recalcula valor total da OS
        await self._recalcular_valor_total(os_id)

        await self.session.flush()
        await self.session.refresh(item)

        return ItemOSResponse.model_validate(item)

    async def apontar_horas(
        self, os_id: int, apontamento_data: ApontamentoHorasCreate
    ) -> ApontamentoHorasResponse:
        """
        Registra apontamento de horas trabalhadas na OS

        Regras:
        - OS deve existir e não estar cancelada
        - Técnico deve existir e estar ativo
        """
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status == StatusOS.CANCELADA:
            raise BusinessRuleException("Não é possível apontar horas em OS cancelada")

        # Valida técnico
        tecnico = await self.tecnico_repo.get_by_id(apontamento_data.tecnico_id)
        if not tecnico:
            raise NotFoundException(f"Técnico {apontamento_data.tecnico_id} não encontrado")
        if not tecnico.ativo:
            raise ValidationException(f"Técnico '{tecnico.nome}' está inativo")

        # Cria apontamento
        apontamento = await self.os_repo.create_apontamento(os_id, apontamento_data)

        await self.session.flush()
        await self.session.refresh(apontamento)

        return ApontamentoHorasResponse.model_validate(apontamento)

    async def finalizar_os(
        self, os_id: int, finalizar_data: FinalizarOSRequest
    ) -> OrdemServicoResponse:
        """
        Finaliza OS (muda status para CONCLUIDA)

        Regras:
        - OS deve estar EM_ANDAMENTO
        - Preenche data_conclusao e descricao_solucao
        - Calcula valor_total final
        """
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status not in [StatusOS.ABERTA, StatusOS.EM_ANDAMENTO]:
            raise BusinessRuleException(
                f"Somente OS ABERTA ou EM_ANDAMENTO pode ser finalizada. Status atual: {os.status.value}"
            )

        # Atualiza dados de conclusão
        os.data_conclusao = finalizar_data.data_conclusao
        os.descricao_solucao = finalizar_data.descricao_solucao
        os.status = StatusOS.CONCLUIDA

        # Recalcula valor total
        await self._recalcular_valor_total(os_id)

        await self.session.flush()
        await self.session.refresh(os)

        return OrdemServicoResponse.model_validate(os)

    async def faturar_os(
        self, os_id: int, faturar_data: FaturarOSRequest
    ) -> OrdemServicoResponse:
        """
        Fatura OS (muda status para FATURADA)

        Regras:
        - OS deve estar CONCLUIDA
        - Cria venda via VendasService (se necessário)
        - Cria conta a receber via FinanceiroService
        - Muda status para FATURADA

        Nota: Este método cria a conta a receber. A venda é opcional.
        """
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status != StatusOS.CONCLUIDA:
            raise BusinessRuleException(
                f"Somente OS CONCLUIDA pode ser faturada. Status atual: {os.status.value}"
            )

        # Calcula valor total final (se ainda não foi calculado)
        if os.valor_total == 0:
            await self._recalcular_valor_total(os_id)
            await self.session.refresh(os)

        valor_final = float(os.valor_total) - faturar_data.desconto

        if valor_final < 0:
            raise ValidationException("Desconto não pode ser maior que o valor total da OS")

        # Cria conta a receber via FinanceiroService
        financeiro_service = FinanceiroService(self.session)

        conta_receber_data = ContaReceberCreate(
            cliente_id=os.cliente_id,
            descricao=f"OS #{os_id} - {os.tipo_servico.nome}",
            categoria="SERVICO",
            valor_original=valor_final,
            data_emissao=datetime.now().date(),
            data_vencimento=datetime.now().date(),  # Pode ser ajustado conforme condição de pagamento
            forma_pagamento=faturar_data.forma_pagamento,
            observacao=faturar_data.observacoes or f"Faturamento da OS #{os_id}",
        )

        await financeiro_service.criar_conta_receber(conta_receber_data)

        # Muda status para FATURADA
        os.status = StatusOS.FATURADA

        await self.session.flush()
        await self.session.refresh(os)

        return OrdemServicoResponse.model_validate(os)

    async def cancelar_os(self, os_id: int, motivo: str) -> OrdemServicoResponse:
        """
        Cancela OS

        Regras:
        - Não pode cancelar OS FATURADA
        - Registra motivo em observações
        - TODO: Implementar devolução de materiais ao estoque
        """
        os = await self.os_repo.get_by_id(os_id)
        if not os:
            raise NotFoundException(f"Ordem de Serviço {os_id} não encontrada")

        if os.status == StatusOS.FATURADA:
            raise BusinessRuleException("Não é possível cancelar OS já faturada")

        if os.status == StatusOS.CANCELADA:
            raise BusinessRuleException("OS já está cancelada")

        # Registra motivo
        os.observacoes = f"{os.observacoes or ''}\n\nCANCELAMENTO: {motivo}".strip()
        os.status = StatusOS.CANCELADA

        # TODO: Implementar devolução automática de materiais ao estoque
        # Para cada item em os.itens, registrar entrada de estoque

        await self.session.flush()
        await self.session.refresh(os)

        return OrdemServicoResponse.model_validate(os)

    async def get_os_abertas(
        self, page: int = 1, page_size: int = 50
    ) -> OrdemServicoList:
        """Lista OSs abertas"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        ordens = await self.os_repo.get_os_abertas(skip=skip, limit=page_size)
        total = await self.os_repo.count(status=StatusOS.ABERTA)
        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrdemServicoList(
            items=[OrdemServicoResponse.model_validate(o) for o in ordens],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_os_atrasadas(
        self, page: int = 1, page_size: int = 50
    ) -> OrdemServicoList:
        """Lista OSs atrasadas (data_prevista < hoje e não concluída)"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        ordens = await self.os_repo.get_os_atrasadas(skip=skip, limit=page_size)

        # Conta total de atrasadas (busca todas e conta)
        todas_atrasadas = await self.os_repo.get_os_atrasadas(skip=0, limit=10000)
        total = len(todas_atrasadas)

        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrdemServicoList(
            items=[OrdemServicoResponse.model_validate(o) for o in ordens],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_agenda_tecnico(
        self,
        tecnico_id: int,
        data_inicio: datetime,
        data_fim: datetime,
        page: int = 1,
        page_size: int = 50,
    ) -> OrdemServicoList:
        """Busca agenda de um técnico por período"""
        # Valida técnico
        tecnico = await self.tecnico_repo.get_by_id(tecnico_id)
        if not tecnico:
            raise NotFoundException(f"Técnico {tecnico_id} não encontrado")

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        ordens = await self.os_repo.get_all(
            skip=skip,
            limit=page_size,
            tecnico_id=tecnico_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        total = await self.os_repo.count(
            tecnico_id=tecnico_id, data_inicio=data_inicio, data_fim=data_fim
        )

        pages = math.ceil(total / page_size) if total > 0 else 1

        return OrdemServicoList(
            items=[OrdemServicoResponse.model_validate(o) for o in ordens],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ====================================
    # MÉTODOS AUXILIARES PRIVADOS
    # ====================================

    async def _recalcular_valor_total(self, os_id: int) -> None:
        """
        Recalcula valor total da OS

        Valor total = valor_mao_obra + soma(itens.total_item)

        Nota: O cálculo de horas (se houver taxa por hora) deve ser
        incluído no valor_mao_obra ou implementado aqui
        """
        valor_total = await self.os_repo.calcular_valor_total(os_id)
        await self.os_repo.atualizar_valor_total(os_id, valor_total)
