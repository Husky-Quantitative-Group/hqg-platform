FROM python:3.12-slim

# Allow proxy configuration during build and runtime.
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ARG http_proxy
ARG https_proxy
ARG no_proxy
ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY
ENV NO_PROXY=$NO_PROXY
ENV http_proxy=$http_proxy
ENV https_proxy=$https_proxy
ENV no_proxy=$no_proxy

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN pip install --no-cache-dir fastapi httpx 'pyjwt[crypto]' uvicorn[standard]

COPY src /app/src

EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.server:app --host 0.0.0.0 --port ${PORT}"]
