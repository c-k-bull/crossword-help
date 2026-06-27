FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

COPY crosshelp ./crosshelp
COPY evals ./evals
COPY tests ./tests
COPY pytest.ini ./

EXPOSE 5001

CMD gunicorn --bind 0.0.0.0:${PORT:-5001} --workers 2 --threads 4 --timeout 60 crosshelp.web:app
