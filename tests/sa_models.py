from citext import CIText
from sqlalchemy import FLOAT, Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class CarParentAssoc(Base):
    __tablename__ = "cartoparent"
    id = Column(Integer, primary_key=True)
    car = relationship("Car")
    parent = relationship("Parent")
    id_car = Column(Integer, ForeignKey("car.car_id"))
    parent_id = Column(Integer, ForeignKey("parent.id"))


class Car(Base):
    __tablename__ = "car"
    car_id = Column(Integer, primary_key=True)
    horsepower = Column(Integer)
    drivers = relationship("Parent", secondary="cartoparent", back_populates="cars")


class Parent(Base):
    __tablename__ = "parent"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    children = relationship("Child", back_populates="parent")
    cars = relationship("Car", secondary="cartoparent", back_populates="drivers")


class Dog(Base):
    __tablename__ = "dog"
    id = Column(Integer, primary_key=True)
    name = Column(String)


class Child(Base):
    __tablename__ = "child"
    key = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    ratio1 = Column(Float)
    ratio2 = Column(FLOAT)
    citextfield = Column(CIText)
    boolfield = Column(Boolean, nullable=False)
    parent_id = Column(Integer, ForeignKey("parent.id"))
    dog_id = Column(Integer)
    parent = relationship(Parent, uselist=False, back_populates="children")
    dog = relationship(
        Dog, primaryjoin="Child.dog_id == Dog.id", foreign_keys=dog_id, backref="owners"
    )
