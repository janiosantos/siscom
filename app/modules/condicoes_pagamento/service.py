"""
Service Layer para Condicoes de Pagamento
"""
from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
import math

from app.modules.condicoes_pagamento.repository import CondicaoPagamentoRepository
from app.modules.condicoes_pagamento.schemas import (
    CondicaoPagamentoCreate,
    CondicaoPagamentoUpdate,
    CondicaoPagamentoResponse,
    CondicaoPagamentoList,
    CalcularParcelasRequest,
    CalcularParcelasResponse,
    ParcelaCalculada,
)
from app.modules.condicoes_pagamento.models import CondicaoPagamento
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    DuplicateException,
)


class CondicaoPagamentoService:
    """Service para regras de negócio de Condições de Pagamento"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CondicaoPagamentoRepository(session)

    async def criar_condicao(
        self, condicao_data: CondicaoPagamentoCreate
    ) -> CondicaoPagamentoResponse:
        """
        Cria uma nova condição de pagamento com parcelas

        Regras:
        - Nome não pode estar duplicado
        - Soma dos percentuais das parcelas deve ser 100%
        - Quantidade de parcelas deve bater com a lista informada
        """
        # Verifica duplicação de nome
        existing = await self.repository.get_by_nome(condicao_data.nome)
        if existing:
            raise DuplicateException(
                f"Condição de pagamento '{condicao_data.nome}' já existe"
            )

        # Valida soma de percentuais (já validado no schema, mas garantindo)
        total_percentual = sum(p.percentual_valor for p in condicao_data.parcelas)
        if abs(total_percentual - 100.0) > 0.01:
            raise ValidationException(
                f"Soma dos percentuais das parcelas deve ser 100%. "
                f"Soma atual: {total_percentual:.2f}%"
            )

        # Cria a condição de pagamento
        condicao = await self.repository.create_condicao(condicao_data)

        # Cria as parcelas
        for parcela_data in condicao_data.parcelas:
            await self.repository.create_parcela(condicao.id, parcela_data)

        # Flush para garantir que parcelas sejam persistidas antes de recarregar
        await self.session.flush()

        # Recarrega com parcelas
        condicao = await self.repository.get_by_id(condicao.id)

        return CondicaoPagamentoResponse.model_validate(condicao)

    async def buscar_condicao(self, condicao_id: int) -> CondicaoPagamentoResponse:
        """Busca condição de pagamento por ID"""
        condicao = await self.repository.get_by_id(condicao_id)
        if not condicao:
            raise NotFoundException(f"Condição de pagamento {condicao_id} não encontrada")

        return CondicaoPagamentoResponse.model_validate(condicao)

    async def listar_condicoes(
        self,
        page: int = 1,
        page_size: int = 50,
        apenas_ativas: bool = False,
    ) -> CondicaoPagamentoList:
        """
        Lista condições de pagamento com paginação

        Args:
            page: Página atual (inicia em 1)
            page_size: Quantidade de itens por página
            apenas_ativas: Se deve listar apenas condições ativas
        """
        if page < 1:
            page = 1

        if page_size < 1 or page_size > 100:
            page_size = 50

        skip = (page - 1) * page_size

        # Busca condições e total
        condicoes = await self.repository.get_all(skip, page_size, apenas_ativas)
        total = await self.repository.count(apenas_ativas)

        # Calcula total de páginas
        pages = math.ceil(total / page_size) if total > 0 else 1

        return CondicaoPagamentoList(
            items=[CondicaoPagamentoResponse.model_validate(c) for c in condicoes],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_condicoes_ativas(self) -> List[CondicaoPagamentoResponse]:
        """Retorna apenas condições de pagamento ativas"""
        condicoes = await self.repository.get_ativas()
        return [CondicaoPagamentoResponse.model_validate(c) for c in condicoes]

    async def atualizar_condicao(
        self, condicao_id: int, condicao_data: CondicaoPagamentoUpdate
    ) -> CondicaoPagamentoResponse:
        """
        Atualiza uma condição de pagamento

        Regras:
        - Se mudar nome, não pode duplicar com existente
        - Se atualizar parcelas, soma de percentuais deve ser 100%
        """
        # Verifica se condição existe
        condicao_atual = await self.repository.get_by_id(condicao_id)
        if not condicao_atual:
            raise NotFoundException(
                f"Condição de pagamento {condicao_id} não encontrada"
            )

        # Verifica duplicação de nome se foi alterado
        if condicao_data.nome and condicao_data.nome != condicao_atual.nome:
            existing = await self.repository.get_by_nome(condicao_data.nome)
            if existing:
                raise DuplicateException(
                    f"Condição de pagamento '{condicao_data.nome}' já existe"
                )

        # Se está atualizando parcelas, valida e atualiza
        if condicao_data.parcelas is not None:
            # Valida soma de percentuais
            total_percentual = sum(p.percentual_valor for p in condicao_data.parcelas)
            if abs(total_percentual - 100.0) > 0.01:
                raise ValidationException(
                    f"Soma dos percentuais das parcelas deve ser 100%. "
                    f"Soma atual: {total_percentual:.2f}%"
                )

            # Remove parcelas antigas
            await self.repository.delete_parcelas_condicao(condicao_id)

            # Cria novas parcelas
            for parcela_data in condicao_data.parcelas:
                await self.repository.create_parcela(condicao_id, parcela_data)

        # Atualiza a condição
        condicao = await self.repository.update(condicao_id, condicao_data)

        # Recarrega com parcelas
        condicao = await self.repository.get_by_id(condicao_id)

        return CondicaoPagamentoResponse.model_validate(condicao)

    async def delete_condicao(self, condicao_id: int) -> bool:
        """
        Inativa uma condição de pagamento (soft delete)

        Regras:
        - Apenas inativa, não deleta do banco
        """
        condicao = await self.repository.get_by_id(condicao_id)
        if not condicao:
            raise NotFoundException(
                f"Condição de pagamento {condicao_id} não encontrada"
            )

        return await self.repository.delete(condicao_id)

    async def calcular_parcelas_venda(
        self, request: CalcularParcelasRequest
    ) -> CalcularParcelasResponse:
        """
        Calcula as parcelas para um valor específico

        Args:
            request: Requisição com condição_id, valor_total e data_base (opcional)

        Returns:
            Resposta com lista de parcelas calculadas (valor e vencimento)
        """
        # Busca a condição de pagamento
        condicao = await self.repository.get_by_id(request.condicao_id)
        if not condicao:
            raise NotFoundException(
                f"Condição de pagamento {request.condicao_id} não encontrada"
            )

        if not condicao.ativa:
            raise ValidationException(
                f"Condição de pagamento '{condicao.nome}' está inativa"
            )

        # Define data base (hoje se não informada)
        data_base = request.data_base if request.data_base else date.today()

        # Calcula parcelas
        parcelas_calculadas: List[ParcelaCalculada] = []

        for parcela in condicao.parcelas:
            # Calcula valor da parcela (converter para float para evitar TypeError com Decimal)
            valor_parcela = round(
                (float(request.valor_total) * float(parcela.percentual_valor)) / 100, 2
            )

            # Calcula data de vencimento
            data_vencimento = data_base + timedelta(days=parcela.dias_vencimento)

            parcelas_calculadas.append(
                ParcelaCalculada(
                    numero_parcela=parcela.numero_parcela,
                    valor=valor_parcela,
                    vencimento=data_vencimento,
                    percentual=parcela.percentual_valor,
                )
            )

        # Ajusta arredondamento para garantir que soma = valor_total
        soma_parcelas = sum(p.valor for p in parcelas_calculadas)
        diferenca = round(float(request.valor_total) - soma_parcelas, 2)

        if diferenca != 0:
            # Adiciona diferença na última parcela
            parcelas_calculadas[-1].valor = round(
                parcelas_calculadas[-1].valor + diferenca, 2
            )

        return CalcularParcelasResponse(
            condicao=CondicaoPagamentoResponse.model_validate(condicao),
            valor_total=request.valor_total,
            parcelas=parcelas_calculadas,
        )
