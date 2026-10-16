#!/usr/bin/env bash
# Builds the core as a shared library for the NuGet package (E199, E200) and copies it to
# OUT/RID/native/, the layout of runtimes/ in the package. Linux builds in manylinux_2_28 for
# glibc 2.28 with libstdc++ linked in, Windows with the static CRT, macOS for macOS 11.
# Usage: build-core-shared.sh RID OUT, run from the repository root.
set -euo pipefail

rid=$1
out=$2
build=build/nuget-$rid
configure=(-DCMAKE_BUILD_TYPE=Release -DSBM_SHARED=ON -DSBM_BUILD_TESTS=OFF)

case $rid in
linux-x64 | linux-arm64)
  image=quay.io/pypa/manylinux_2_28_$(uname -m)
  # The image has CMake as a Python package only; the build directory belongs to root.
  docker run --rm -v "$PWD:/io" -w /io "$image" bash -euo pipefail -c "
    /opt/python/cp312-cp312/bin/pip install --quiet cmake==3.31.6
    cmake=/opt/python/cp312-cp312/bin/cmake
    \$cmake -S sdk/core -B $build ${configure[*]} \
      '-DCMAKE_SHARED_LINKER_FLAGS=-static-libstdc++ -static-libgcc -s'
    \$cmake --build $build -j 4
    chown -R $(id -u):$(id -g) $build"
  library=$build/lib/libsbm.so
  readelf -d "$library" | grep NEEDED
  if readelf -d "$library" | grep -q 'libstdc++'; then
    echo "error: $library needs libstdc++" >&2
    exit 1
  fi
  newest=$(objdump -T "$library" | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1)
  echo "newest glibc symbol: $newest"
  if [ "$(printf '%s\n' "$newest" GLIBC_2.28 | sort -V | tail -1)" != GLIBC_2.28 ]; then
    echo "error: $library needs $newest, more than glibc 2.28" >&2
    exit 1
  fi
  ;;
win-x64)
  cmake -S sdk/core -B "$build" "${configure[@]}" -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded
  cmake --build "$build" --config Release
  library=$build/bin/Release/sbm.dll
  ;;
osx-x64 | osx-arm64)
  cmake -S sdk/core -B "$build" "${configure[@]}" -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
  cmake --build "$build" -j 4
  library=$build/lib/libsbm.dylib
  otool -L "$library"
  otool -l "$library" | grep -A3 LC_BUILD_VERSION
  ;;
*)
  echo "error: unknown runtime identifier $rid" >&2
  exit 2
  ;;
esac

mkdir -p "$out/$rid/native"
cp "$library" "$out/$rid/native/"
ls -l "$out/$rid/native"
