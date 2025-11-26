import random
from sqlalchemy.exc import IntegrityError
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Operator, SourceOperatorLink, Interaction, InteractionStatus, Lead

async def get_or_create_lead(session: AsyncSession, external_id: str) -> Lead:
    """
    Получает существующего лида или создает нового по внешнему ID.

    Реализует безопасный паттерн "Get or Create". Если между проверкой
    существования и вставкой происходит вставка в параллельной транзакции
    (Race Condition), перехватывает IntegrityError, делает откат и
    возвращает уже созданную запись.

    :param session: Сессия базы данных.
    :param external_id: Уникальный идентификатор лида из внешней системы.
    :return: Объект модели Lead.
    """
    stmt = select(Lead).where(Lead.external_id == external_id)
    lead = await session.scalar(stmt)
    
    if lead:
        return lead

    try:
        lead = Lead(external_id=external_id)
        session.add(lead)
        await session.flush()
        return lead
    except IntegrityError:
        await session.rollback()
        lead = await session.scalar(stmt)
        return lead

async def select_operator_for_source(session: AsyncSession, source_id: int) -> Optional[Operator]:
    """
    Выбирает подходящего оператора для заявки с указанного источника.

    Алгоритм распределения:
    1. Через CTE считает текущую нагрузку (OPEN тикеты) для каждого оператора.
    2. Выбирает операторов, которые привязаны к источнику (SourceOperatorLink) и активны (is_active=True).
    3. Исключает перегруженных операторов (current_load >= max_load).
    4. Из оставшихся кандидатов выбирает одного случайным образом, используя веса (weight) для вероятностного распределения.

    :param session: Сессия базы данных.
    :param source_id: ID источника, откуда пришла заявка.
    :return: Объект Operator или None, если нет доступных/свободных операторов.
    """
    load_subquery = (
        select(Interaction.operator_id, func.count(Interaction.id).label("current_load"))
        .where(Interaction.status == InteractionStatus.OPEN)
        .group_by(Interaction.operator_id)
        .cte("load_subquery")
    )

    stmt = (
        select(Operator, SourceOperatorLink.weight, func.coalesce(load_subquery.c.current_load, 0))
        .join(SourceOperatorLink, Operator.id == SourceOperatorLink.operator_id)
        .outerjoin(load_subquery, Operator.id == load_subquery.c.operator_id)
        .where(
            SourceOperatorLink.source_id == source_id,
            Operator.is_active == True
        )
    )

    result = await session.execute(stmt)
    candidates_data = result.all()

    valid_candidates = []
    valid_weights = []

    for op, weight, current_load in candidates_data:
        if current_load < op.max_load:
            valid_candidates.append(op)
            valid_weights.append(weight)

    if not valid_candidates:
        return None

    return random.choices(valid_candidates, weights=valid_weights, k=1)[0]