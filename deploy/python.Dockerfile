# syntax=docker/dockerfile:1
# Images for the Python services; the build context is the repository root.
# Target services: migrate and api. Target runner: adds nsjail, the sandbox configuration and the
# runtime directory the bots run in (sandbox.md).

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

# nsjail from a fixed commit of its release 3.6 (E86).
FROM python:3.12-slim AS nsjail
ARG NSJAIL_COMMIT=f78475530b46d0186111a9096b30725f816b55fe
RUN apt-get update \
    && apt-get install -y --no-install-recommends autoconf bison ca-certificates flex g++ gcc git \
       libnl-route-3-dev libprotobuf-dev libtool make pkg-config protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*
RUN git init -q /nsjail \
    && git -C /nsjail fetch -q --depth 1 https://github.com/google/nsjail "$NSJAIL_COMMIT" \
    && git -C /nsjail checkout -q FETCH_HEAD \
    && make -C /nsjail -j"$(nproc)" \
    && strip /nsjail/nsjail

# The Python the bots run with, pinned (E31, E86); the core is compiled a second time for it.
FROM python:3.14.8-slim-trixie AS bot-python-build
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY sdk/core sdk/core
COPY sdk/python sdk/python
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels ./sdk/python

# Without a compiler: this tree becomes the read-only root of every Python bot.
FROM python:3.14.8-slim-trixie AS bot-python
RUN --mount=type=bind,from=bot-python-build,source=/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*.whl \
    && pip uninstall -y -q pip \
    && python -m compileall -q -j 0 /usr/local/lib/python3.14
# Only what Python needs: interpreter, libraries, the loader and its cache. The mount points of
# the jail exist as empty directories and files, since the root is mounted read-only.
RUN mkdir -p /rt/usr/lib /rt/etc /rt/dev /rt/bot \
    && cp -a /usr/local /rt/usr/local \
    && cp -a /usr/lib/x86_64-linux-gnu /usr/lib64 /rt/usr/lib/ \
    && mv /rt/usr/lib/lib64 /rt/usr/lib64 \
    && ln -s usr/lib /rt/lib \
    && ln -s usr/lib64 /rt/lib64 \
    && cp /etc/ld.so.cache /rt/etc/ \
    && touch /rt/dev/null /rt/dev/urandom

FROM python:3.12-slim AS services
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin sbm
RUN --mount=type=bind,from=build,source=/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*.whl
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
USER sbm
WORKDIR /tmp

# Runs as root with a few capabilities (compose.yaml); bots only ever run inside nsjail.
FROM services AS runner
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends libnl-route-3-200 libprotobuf32t64 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=nsjail /nsjail/nsjail /usr/local/bin/nsjail
COPY --from=bot-python /rt /opt/sbm/runtimes/python
COPY sandbox /opt/sbm/sandbox
# The bot directory of the reference bots, which live in the SDK of the runtime.
RUN mkdir /opt/sbm/no-files
ENV SBM_SANDBOX=nsjail
