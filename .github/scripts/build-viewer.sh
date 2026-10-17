#!/usr/bin/env bash
# Builds the viewer program sbm-viewer for the NuGet package (E106, E206) and copies it with the
# licenses of its parts to OUT/RID/native/, the layout of runtimes/ in the package. Linux builds
# in manylinux_2_28 for glibc 2.28 with libstdc++ linked in, Windows with the static CRT, macOS
# for macOS 11, as build-core-shared.sh does for the core.
# Usage: build-viewer.sh RID OUT, run from the repository root.
set -euo pipefail

rid=$1
out=$2
build=build/viewer-$rid
prefix=$build/install
configure=(-DCMAKE_BUILD_TYPE=Release -DSBM_VIEWER_BUILD_TESTS=OFF
  -DSBM_VIEWER_INSTALL_DIR=bin -DSBM_VIEWER_LICENSE_DIR=bin/sbm-viewer-licenses)

case $rid in
linux-x64 | linux-arm64)
  image=quay.io/pypa/manylinux_2_28_$(uname -m)
  # SDL3 needs the X11 headers to build with a window system; it loads the libraries at run
  # time. The image has CMake as a Python package only; the build directory belongs to root.
  docker run --rm -v "$PWD:/io" -w /io "$image" bash -euo pipefail -c "
    dnf install -y -q libX11-devel libXext-devel libXcursor-devel libXi-devel \
      libXrandr-devel libXfixes-devel
    /opt/python/cp312-cp312/bin/pip install --quiet cmake==3.31.6
    cmake=/opt/python/cp312-cp312/bin/cmake
    \$cmake -S sdk/viewer -B $build ${configure[*]} \
      '-DCMAKE_EXE_LINKER_FLAGS=-static-libstdc++ -static-libgcc -s'
    \$cmake --build $build -j 4
    \$cmake --install $build --prefix $prefix
    chown -R $(id -u):$(id -g) $build"
  program=$prefix/bin/sbm-viewer
  readelf -d "$program" | grep NEEDED
  if readelf -d "$program" | grep -q 'libstdc++'; then
    echo "error: $program needs libstdc++" >&2
    exit 1
  fi
  newest=$(objdump -T "$program" | grep -o 'GLIBC_[0-9.]*' | sort -uV | tail -1)
  echo "newest glibc symbol: $newest"
  if [ "$(printf '%s\n' "$newest" GLIBC_2.28 | sort -V | tail -1)" != GLIBC_2.28 ]; then
    echo "error: $program needs $newest, more than glibc 2.28" >&2
    exit 1
  fi
  ;;
win-x64)
  cmake -S sdk/viewer -B "$build" "${configure[@]}"
  cmake --build "$build" --config Release
  cmake --install "$build" --config Release --prefix "$prefix"
  ;;
osx-x64 | osx-arm64)
  cmake -S sdk/viewer -B "$build" "${configure[@]}" -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0
  cmake --build "$build" -j 4
  cmake --install "$build" --prefix "$prefix"
  otool -L "$prefix/bin/sbm-viewer"
  otool -l "$prefix/bin/sbm-viewer" | grep -A3 LC_BUILD_VERSION
  ;;
*)
  echo "error: unknown runtime identifier $rid" >&2
  exit 2
  ;;
esac

mkdir -p "$out/$rid/native"
cp -R "$prefix/bin/." "$out/$rid/native/"
ls -lR "$out/$rid/native"
