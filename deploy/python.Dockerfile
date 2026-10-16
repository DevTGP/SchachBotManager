# syntax=docker/dockerfile:1
# Images for the Python services; the build context is the repository root.
# Target services: migrate, api and gateway. Target runner (also the play runner): adds nsjail, the sandbox configuration and the
# runtime directory the bots run in (sandbox.md).

FROM python:3.12-slim AS build
# The SDK compiles the C++ core; CMake and Ninja come from PyPI through scikit-build-core.
RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY sdk/core sdk/core
COPY sdk/python sdk/python
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -C cmake.define.SBM_VIEWER=OFF ./sdk/python
COPY services/store services/store
COPY services/runner services/runner
COPY services/gateway services/gateway
COPY backend backend
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels \
    ./services/store ./services/runner ./services/gateway ./backend

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
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -C cmake.define.SBM_VIEWER=OFF ./sdk/python

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
    && touch /rt/dev/null

# C# bots (E192): the native host that starts .NET without /proc (E205), the core as a shared
# library, the launcher every bot runs in and the build tool that analyzes and compiles an upload
# at verification (E203, E204), plus the reference assemblies it compiles against. No MSBuild and
# no NuGet at run time.
FROM mcr.microsoft.com/dotnet/sdk:10.0.402 AS bot-csharp-build
RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake g++ make \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY sdk/core sdk/core
COPY sdk/csharp sdk/csharp
RUN cmake -S sdk/core -B build/core -DCMAKE_BUILD_TYPE=Release -DSBM_BUILD_TESTS=OFF \
    && cmake --build build/core -j"$(nproc)"
RUN dotnet publish sdk/csharp/server/Sbm.Launcher -c Release -o /out/launch --no-self-contained \
    && dotnet publish sdk/csharp/server/Sbm.Build -c Release -o /out/build --no-self-contained \
    && mkdir -p /out/refs/net /out/refs/sdk \
    && cp /usr/share/dotnet/packs/Microsoft.NETCore.App.Ref/*/ref/net10.0/*.dll /out/refs/net/ \
    && cp /out/launch/SchachBotManager.dll /out/refs/sdk/ \
    && find /out -name '*.xml' -delete \
    && gcc -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror -pthread \
       -o /out/host sdk/csharp/server/Sbm.Host/sbm-host.c -ldl

# The .NET runtime of the same release as the reference assemblies; this tree becomes the
# read-only root of every C# bot and of the build tool.
FROM mcr.microsoft.com/dotnet/runtime:10.0.13 AS bot-csharp
COPY --from=bot-csharp-build /out /out
RUN mkdir -p /rt/usr/lib /rt/usr/share /rt/etc /rt/dev /rt/bot /rt/program /rt/sbm \
    && cp -a /usr/share/dotnet /rt/usr/share/dotnet \
    && cp -a /usr/lib/x86_64-linux-gnu /usr/lib64 /rt/usr/lib/ \
    && mv /rt/usr/lib/lib64 /rt/usr/lib64 \
    && ln -s usr/lib /rt/lib \
    && ln -s usr/lib64 /rt/lib64 \
    && cp /etc/ld.so.cache /rt/etc/ \
    && touch /rt/dev/null /rt/dev/urandom \
    && cp -a /out/host /out/launch /out/build /out/refs /rt/sbm/

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
COPY --from=bot-csharp /rt /opt/sbm/runtimes/csharp
COPY sandbox /opt/sbm/sandbox
# The bot directory of the reference bots, which live in the SDK of the runtime.
RUN mkdir /opt/sbm/no-files
ENV SBM_SANDBOX=nsjail
