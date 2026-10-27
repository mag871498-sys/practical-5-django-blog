#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
if curl --silent --fail http://127.0.0.1:8005/ >/dev/null; then
    open http://127.0.0.1:8005/
    exit 0
fi
if [[ ! -x .venv/bin/python ]]; then
    python3 -m venv .venv || exit 1
    .venv/bin/python -m pip install -r requirements.txt || exit 1
fi
.venv/bin/python scripts/bootstrap.py || exit 1
open http://127.0.0.1:8005/
exec .venv/bin/python manage.py runserver 127.0.0.1:8005
