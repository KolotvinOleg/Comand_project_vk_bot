from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import user_name, password, data_base


Base = declarative_base()



class Vk_User(Base):

    __tablename__ = "vk_user"

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True)
    first_name = Column(String(40), nullable=False)
    last_name = Column(String(40), nullable=False)
    age = Column(Integer, nullable=False)
    city_id = Column(Integer, nullable=False)
    city_title = Column(String(40), nullable=False)
    gender = Column(String, nullable=False)


class Vk_User_favourite_user(Base):

    __tablename__ = "vk_user_favourite_user"

    id = Column(Integer, primary_key=True)
    id_vk_user = Column(Integer, ForeignKey("vk_user.id"), nullable=False)
    id_favourite_user = Column(Integer, ForeignKey("favourite_user.id"), nullable=False)

    vk_user = relationship(Vk_User, backref="vk_user_favourite_user")

class Favourite_user(Base):
    __tablename__ = "favourite_user"

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True)
    first_name = Column(String(40), nullable=False)
    last_name = Column(String(40), nullable=False)
    age = Column(Integer, nullable=False)
    city_id = Column(Integer, nullable=False)
    city_title = Column(String(40), nullable=False)
    gender = Column(String, nullable=False)
    # id_vk_user = Column(Integer, ForeignKey("vk_user.id"), nullable=False)

    # vk_user = relationship(Vk_User, backref="favourite_user")

class Photo(Base):
    __tablename__ = "photo"

    id = Column(Integer, primary_key=True)
    media_id = Column(Integer, nullable=False)
    id_favourite_user = Column(Integer, ForeignKey("favourite_user.id"), nullable=False)

    favourite_user = relationship(Favourite_user, backref="photo")


DSN = f'postgresql://{user_name}:{password}@localhost:5432/{data_base}'
engine = create_engine(DSN)
Session = sessionmaker(bind=engine)
session = Session()

def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

def insert_vk_user(session, data_user: dict):
    user = Vk_User(**data_user)
    session.add(user)
    session.commit()

def insert_favourite_user(session, data_user: dict):
    user = Favourite_user(**data_user)
    session.add(user)
    session.commit()

def insert_vk_user_favourite_user(session, vk_user_id, favourite_user_id):
    relation = Vk_User_favourite_user(id_vk_user=vk_user_id, id_favourite_user=favourite_user_id)
    session.add(relation)
    session.commit()

def insert_photo(session, media_id, id_favourite_user):
    photo_dct = {"media_id": media_id, "id_favourite_user": id_favourite_user}
    photo = Photo(**photo_dct)
    session.add(photo)
    session.commit()


if __name__ == "__main__":
    create_tables(engine)

