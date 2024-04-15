from __future__ import annotations  # needed so that update_or_create can define School return type

import logging
import os
from datetime import datetime

from geoalchemy2 import Geometry, WKTElement
from sqlalchemy import String, Column, JSON, DateTime, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from jedeschule.items import School as SchoolItem
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
    update_timestamp = Column(DateTime, onupdate=func.now())
    location = Column(Geometry('POINT'))

    @staticmethod
    def update_or_create(item: SchoolPipelineItem, session=None) -> School:
        if not session:
            session = get_session()

        school_data = {**item.info}
        school = session.query(School).get(item.info['id'])
        latitude = school_data.pop('latitude', None)
        longitude = school_data.pop('longitude', None)
        if latitude is not None and longitude is not None:
            location = WKTElement(f"POINT({longitude} {latitude})", srid=4326)
            school_data['location'] = location
        if school:
            session.query(School).filter_by(id=item.info['id']).update({**school_data, 'raw': item.item})
        else:
            school = School(**school_data, raw=item.item)
        return school

    def __str__(self):
        return f'<School id={self.id}, name={self.name}>'


class DatabasePipeline:
    def __init__(self):
        self.session = get_session()

    def process_item(self, item: SchoolPipelineItem, spider):
        school = School.update_or_create(item, session=self.session)
        try:
            self.session.add(school)
            self.session.commit()
        except SQLAlchemyError as e:
            logging.warning('Error when putting to DB')
            logging.warning(e)
            self.session.rollback()
        return school
