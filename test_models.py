import os
import unittest
from unittest import mock

from scrapy import Item
from scrapy.item import Field

from jedeschule.items import School
from jedeschule.pipelines.school_pipeline import SchoolPipelineItem
from jedeschule.pipelines.db_pipeline import School as DBSchool, get_session


class TestSchoolItem(Item):
    name = Field()
    nr = Field()


@mock.patch.dict(os.environ, {'DATABASE_URL': 'sqlite://'})
class TestSchool(unittest.TestCase):
    def test_import_new(self):
        # Arrange
        info = School(name='Test Schule', id='NDS-1')
        item = dict(name='Test Schule', nr=1)
        school_item: SchoolPipelineItem = SchoolPipelineItem(info=info, item=item)
        db_item = DBSchool.update_or_create(school_item)
        session = get_session()
        session.add(db_item)
        session.commit()

        # Act
        count = session.query(DBSchool).count()

        # Assert
        self.assertEqual(count, 1)

    def test_import_existing(self):
        # This test requires the previous one to have run already so that the item
        # exists in the database
        # Arrange
        info = School(name='Test Schule (updated)', id='NDS-1')
        item = dict(name='Test Schule', nr=1)
        school_item: SchoolPipelineItem = SchoolPipelineItem(info=info, item=item)
        db_item = DBSchool.update_or_create(school_item)
        session = get_session()
        session.add(db_item)
        session.commit()

        # Act
        count = session.query(DBSchool).count()
        db_school = session.query(DBSchool).first()

        # Assert
        self.assertEqual(count, 1)
        self.assertEqual(db_school.name, "Test Schule (updated)")


if __name__ == '__main__':
    unittest.main()
