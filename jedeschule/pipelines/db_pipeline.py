import os

from scrapy.exceptions import DropItem
from sqlalchemy import String, Column, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jedeschule.items import School


Base = declarative_base()
engine = create_engine(os.environ.get("DATABASE_URL"), echo=True)
Session = sessionmaker(bind=engine)
session = Session()


class School(Base):
    __tablename__ = 'schools'
    id = Column(String, primary_key=True)
    name = Column(String)
    address = Column(String)
    website = Column(String)
    email = Column(String)
    school_type = Column(String)
    legal_status = Column(String)
    provider = Column(String)
    fax = Column(String)
    phone = Column(String)
    raw = Column(JSON)


class DatabasePipeline(object):
    def process_item(self, item, spider):
        school = School(**item['info'], raw=item['item'])
        session.add(school)
        session.commit()
