#!/bin/sh
# Build engine capabilities explicitly; never substitute CPU binaries for CUDA.
set -eu
profile=$1
case "$profile" in *-cuda) gpu=ON ;; *) gpu=OFF ;; esac
export CMAKE_BUILD_PARALLEL_LEVEL=4
case "$profile" in
  gromacs*|lammps*)
    mkdir -p /tmp/plumed
    tar -xf /tmp/physics-source/plumed.tar.gz -C /tmp/plumed --strip-components=1
    cd /tmp/plumed
    ./configure --prefix=/usr/local --disable-mpi --enable-shared
    make -j4
    make install
    ldconfig
    ;;
esac
case "$profile" in
  gromacs*)
    mkdir -p /tmp/engine
    tar -xf /tmp/physics-source/gromacs.tar.gz -C /tmp/engine --strip-components=1
    if [ "$gpu" = ON ]; then backend=CUDA; else backend=OFF; fi
    cmake -S /tmp/engine -B /tmp/engine/build -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_LIBDIR=lib -DGMX_GPU="$backend" -DGMX_CUDA_TARGET_SM=75 -DGMX_MPI=OFF \
      -DGMX_BUILD_OWN_FFTW=OFF -DGMX_FFT_LIBRARY=fftw3 -DGMX_SIMD=SSE2 -DGMX_USE_PLUMED=ON
    cmake --build /tmp/engine/build
    cmake --install /tmp/engine/build
    ;;
  lammps*)
    mkdir -p /tmp/engine
    tar -xf /tmp/physics-source/lammps.tar.gz -C /tmp/engine --strip-components=1
    if [ "$gpu" = ON ]; then
      set -- -DPKG_KOKKOS=ON -DKokkos_ENABLE_CUDA=ON -DKokkos_ARCH_TURING75=ON \
        -DCMAKE_CXX_COMPILER=/tmp/engine/lib/kokkos/bin/nvcc_wrapper
    else
      set --
    fi
    cmake -S /tmp/engine/cmake -B /tmp/engine/build -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_MPI=OFF -DPKG_PLUMED=ON -DDOWNLOAD_PLUMED=OFF -DPLUMED_MODE=shared "$@"
    cmake --build /tmp/engine/build
    cmake --install /tmp/engine/build
    ;;
  hoomd*)
    git clone --recursive --depth 1 --branch v5.2.0 https://github.com/glotzerlab/hoomd-blue.git /tmp/engine
    cmake -S /tmp/engine -B /tmp/engine/build -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/physics -DPython_EXECUTABLE=/opt/physics/bin/python \
      -Dpybind11_DIR="$(python -m pybind11 --cmakedir)" \
      -DENABLE_GPU="$gpu" -DCUDA_ARCH_LIST=75 -DENABLE_MPI=OFF
    cmake --build /tmp/engine/build
    cmake --install /tmp/engine/build
    ;;
  *) echo "Unknown source profile: $profile" >&2; exit 2 ;;
esac
ldconfig
rm -rf /tmp/engine /tmp/plumed /tmp/physics-source
