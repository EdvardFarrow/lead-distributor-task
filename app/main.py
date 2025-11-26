from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db, init_models
from .models import Operator, Source, SourceOperatorLink, Interaction, InteractionStatus
from .schemas import (
    OperatorCreate, OperatorRead, 
    SourceCreate, SourceConfigUpdate, 
    InteractionCreate, InteractionRead
)
from .services import get_or_create_lead, select_operator_for_source
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    yield

app = FastAPI(title="CRM Distributor", lifespan=lifespan)
@app.post("/operators/", response_model=OperatorRead)
async def create_operator(op: OperatorCreate, db: AsyncSession = Depends(get_db)):
    new_op = Operator(**op.model_dump())
    db.add(new_op)
    await db.commit()
    await db.refresh(new_op)
    return new_op

@app.post("/sources/", response_model=dict)
async def create_source(source: SourceCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрирует новый источник лидов (Source).

    :param source: Данные источника (название).
    :return: Словарь с ID и названием созданного источника.
    """
    new_source = Source(name=source.name)
    db.add(new_source)
    await db.commit()
    return {"id": new_source.id, "name": new_source.name}

@app.post("/sources/{source_id}/config")
async def configure_source_weights(
    source_id: int, 
    configs: List[SourceConfigUpdate], 
    db: AsyncSession = Depends(get_db)
):
    """
    Настраивает веса распределения для конкретного источника.

    Обновляет или создает связи между источником и операторами,
    устанавливая вес (приоритет) получения заявок.
    Использует `merge` для обновления существующих записей.
    
    :param source_id: ID источника.
    :param configs: Список конфигураций (ID оператора и вес).
    """
    
    for conf in configs:
        link = SourceOperatorLink(
            source_id=source_id, 
            operator_id=conf.operator_id, 
            weight=conf.weight
        )
        await db.merge(link)
    
    await db.commit()
    return {"status": "updated"}

@app.post("/interactions/", response_model=InteractionRead)
async def register_interaction(
    data: InteractionCreate, 
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрирует новое взаимодействие (лид) и распределяет его.

    Алгоритм:
    1. Находит или создает лида (Lead) по внешнему ID.
    2. Выбирает подходящего оператора для указанного источника 
    (с учетом весов и текущей нагрузки).
    3. Создает запись взаимодействия со статусом OPEN.

    :return: Созданный объект Interaction.
    """
    lead = await get_or_create_lead(db, data.external_lead_id)

    chosen_operator = await select_operator_for_source(db, data.source_id)
    
    interaction = Interaction(
        lead_id=lead.id,
        source_id=data.source_id,
        operator_id=chosen_operator.id if chosen_operator else None,
        status=InteractionStatus.OPEN
    )
    
    db.add(interaction)
    await db.commit()
    await db.refresh(interaction)
    
    return interaction

@app.get("/stats/")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """
    Получает сводную статистику по загрузке операторов.

    Возвращает список операторов с их максимальной нагрузкой
    и текущим количеством активных тикетов (статус OPEN).
    Выполняется за один SQL-запрос (оптимизировано N+1).

    :return: Список словарей со статистикой.
    """
    query = (
        select(
            Operator.name,
            Operator.max_load,
            Operator.is_active,
            func.count(Interaction.id).label("current_load")
        )
        .outerjoin(
            Interaction, 
            (Operator.id == Interaction.operator_id) & 
            (Interaction.status == InteractionStatus.OPEN)
        )
        .group_by(Operator.id)
    )

    result = await db.execute(query)
    rows = result.all()

    stats = [
        {
            "operator": row.name,
            "max_load": row.max_load,
            "current_load": row.current_load, 
            "is_active": row.is_active
        }
        for row in rows
    ]
    
    return stats


