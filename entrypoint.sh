#!/bin/sh
set -eu

alembic upgrade head || {
  echo "Migrations failed"
  exit 1
}

python -m app || {
  echo "Application failed"
  exit 1
}
