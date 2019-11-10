from jedeschule.pipelines.db_pipeline import engine, Base

Base.metadata.create_all(engine)