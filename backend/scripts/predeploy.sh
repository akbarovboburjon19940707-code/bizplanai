#!/bin/sh
# Render preDeployCommand: Render buyruqni shell'siz ishga tushiradi, shuning uchun && va qo'shtirnoqlar shu yerda.
set -e
cd /app
alembic upgrade head
python -m app.cli seed
