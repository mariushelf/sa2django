from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SAParent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("SAChild", back_populates="parent")


class SAChild(Base):
    __tablename__ = "child"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    parent_id = Column(Integer, ForeignKey("parent.id"))
    parent = relationship(SAParent, uselist=False, back_populates="children")
