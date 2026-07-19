FROM mcr.microsoft.com/devcontainers/python:1-3.11-bookworm

ARG POETRY_VERSION=2.3.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

RUN pipx install "poetry==${POETRY_VERSION}"

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
