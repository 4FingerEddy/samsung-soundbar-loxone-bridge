FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --chown=app:app requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app ./app
RUN chmod -R u=rwX,g=rX,o=rX /app/app

USER app
EXPOSE 8088

CMD uvicorn app.main:app --host "${BRIDGE_HOST:-127.0.0.1}" --port "${BRIDGE_PORT:-8088}"
