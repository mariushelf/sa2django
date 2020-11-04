from sqlalchemy import FLOAT, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from citext import CIText

Base = declarative_base()


class SAParent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("SAChild", back_populates="parent")


class SAChild(Base):
    __tablename__ = "child"
    key = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    ratio1 = Column(Float)
    ratio2 = Column(FLOAT)
    citextfield = Column(CIText)
    boolfield = Column(Boolean, nullable=False)
    parent_id = Column(Integer, ForeignKey("parent.id"))
    parent = relationship(SAParent, uselist=False, back_populates="children")
