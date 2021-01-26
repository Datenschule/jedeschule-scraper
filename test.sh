#!/bin/sh

set -e

touch /tmp/jedeschule-test.sqlite

export DATABASE_URL=sqlite:////tmp/jedeschule-test.sqlite
alembic upgrade head
python test_models.py

rm /tmp/jedeschule-test.sqlite
