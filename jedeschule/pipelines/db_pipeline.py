import logging
import os

from sqlalchemy import String, Column, JSON
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jedeschule.items import School
from jedeschule.pipelines.school_pipeline import SchoolPipelineItem

Base = declarative_base()


def get_session():
    engine = create_engine(os.environ.get("DATABASE_URL"), echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()

    return session


class School(Base):
    __tablename__ = 'schools'
    id = Column(String, primary_key=True)
    name = Column(String)
    address = Column(String)
    address2 = Column(String)
    zip = Column(String)
    city = Column(String)
    website = Column(String)
    email = Column(String)
    school_type = Column(String)
    legal_status = Column(String)
    provider = Column(String)
    fax = Column(String)
    phone = Column(String)
    director = Column(String)
    raw = Column(JSON)

    @staticmethod
    def update_or_create(item: SchoolPipelineItem) -> School:
        session = get_session()

        school = session.query(School).get(item.info['id'])
        if school:
            session.query(School).filter_by(id=item.info['id']).update({**item.info, 'raw': item.item})
        else:
            school = School(**item.info, raw=item.item)
        return school


class DatabasePipeline(object):
    def process_item(self, item, spider):
        school = School.update_or_create(item)
        try:
            session = get_session()
            session.add(school)
            session.commit()
        except SQLAlchemyError as e:
            logging.warning('Error when putting to DB')
            logging.warning(e)
            session.rollback()
        return school
