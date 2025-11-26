import enum
from typing import List, Optional
from sqlalchemy import Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class SourceOperatorLink(Base):
    __tablename__ = "source_operator_links"
    
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=0, comment="Вес (доля трафика)")

    operator: Mapped["Operator"] = relationship(back_populates="source_links")
    source: Mapped["Source"] = relationship(back_populates="operator_links")

class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_load: Mapped[int] = mapped_column(Integer, default=10)

    source_links: Mapped[List[SourceOperatorLink]] = relationship(back_populates="operator")
    interactions: Mapped[List["Interaction"]] = relationship(back_populates="operator")

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)

    operator_links: Mapped[List[SourceOperatorLink]] = relationship(back_populates="source")

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String, unique=True, index=True)

class InteractionStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"

class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("operators.id"), nullable=True)
    status: Mapped[InteractionStatus] = mapped_column(default=InteractionStatus.OPEN)

    operator: Mapped["Operator"] = relationship(back_populates="interactions")