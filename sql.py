from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


Base = declarative_base()
engine = create_engine("sqlite:///message.db")
session = sessionmaker(bind=engine)()

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    qqId = Column(Integer)
    telegramId = Column(Integer)

def append(qqId, telegramId):
    message = Message(qqId=qqId, telegramId=telegramId)
    session.add(message)

def queryByQQId(qqId):
    return session.query(Message).filter_by(qqId=qqId).first().telegramId

def queryByTgId(tgId):
    return session.query(Message).filter_by(telegramId=tgId).first().qqId

Base.metadata.create_all(engine, checkfirst=True)