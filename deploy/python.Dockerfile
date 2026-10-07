# syntax=docker/dockerfile:1
# One image for the Python services (migrate, runner, api); the build context is the repository root.

FROM python:3.12-slim AS build
# The SDK compiles the C++ core; CMake and Ninja come from PyPI through scikit-build-core.
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY sdk/core sdk/core
COPY sdk/python sdk/python
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels ./sdk/python
COPY services/store services/store
COPY services/runner services/runner
COPY backend backend
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels ./services/store ./services/runner ./backend

FROM python:3.12-slim
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin sbm
RUN --mount=type=bind,from=build,source=/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*.whl
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER sbm
WORKDIR /tmp
