# The runner image with what the negative suite needs on top (sandbox.md, E88): pytest and the
# C# test bots. They are compiled with the .NET SDK, not with sbm-build, because the sandbox must
# hold on its own against what the analysis would reject; the launcher runs each bot.dll as it
# runs a verified program. Built by run-in-docker.sh from the repository root.
ARG RUNNER=sbm-runner

FROM mcr.microsoft.com/dotnet/sdk:10.0.402 AS csharp-bots
WORKDIR /src
COPY sdk/core/CMakeLists.txt sdk/core/CMakeLists.txt
COPY sdk/csharp sdk/csharp
COPY services/runner/tests/sandbox/bots/csharp services/runner/tests/sandbox/bots/csharp
WORKDIR /src/services/runner/tests/sandbox/bots/csharp
RUN set -e; for project in */*.csproj; do \
        name=$(dirname "$project"); \
        dotnet build "$project" -c Release -o "/build/$name"; \
        mkdir -p "/bots/$name"; \
        cp "/build/$name/bot.dll" "/bots/$name/"; \
    done

FROM ${RUNNER}
RUN pip install --no-cache-dir pytest==9.1.1
COPY --from=csharp-bots /bots /opt/sbm-suite/csharp
