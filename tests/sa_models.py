from citext import CIText
from sqlalchemy import FLOAT, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SACarParentAssoc(Base):
    __tablename__ = "cartoparent"
    id = Column(Integer, primary_key=True)
    car_id = Column(Integer, ForeignKey("car.car_id"))
    parent_id = Column(Integer, ForeignKey("parent.id"))


class SACar(Base):
    __tablename__ = "car"
    car_id = Column(Integer, primary_key=True)
    horsepower = Column(Integer)
    drivers = relationship("SAParent", secondary="cartoparent", back_populates="cars")


class SAParent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("SAChild", back_populates="parent")
    cars = relationship(
        "SACar", secondary=SACarParentAssoc.__table__, back_populates="drivers"
    )


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
