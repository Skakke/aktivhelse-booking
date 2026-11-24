#!/bin/sh
# Oppdaterer databaseskjemaet og legger inn testdata før appen starter.
set -e

echo "Kjører databasemigreringer ..."
alembic upgrade head

echo "Legger inn testdata (hvis databasen er tom) ..."
python -m app.seed

exec "$@"
