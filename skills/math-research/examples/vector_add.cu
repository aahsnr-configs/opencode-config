#include <cuda_runtime.h>
#include <cmath>
#include <cstdio>
#include <cstdlib>

#define CUDA_CHECK(call) do { cudaError_t status = (call); if (status != cudaSuccess) { std::fprintf(stderr, "%s\n", cudaGetErrorString(status)); std::exit(2); } } while (0)

__global__ void vector_add(const double *a, const double *b, double *c, int count) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i < count) c[i] = a[i] + b[i];
}

int main() {
    constexpr int n = 1025;
    double a[n], b[n], c[n];
    for (int i = 0; i < n; ++i) { a[i] = i * 0.5; b[i] = 1.0 - i * 0.25; }
    double *da, *db, *dc;
    CUDA_CHECK(cudaMalloc(&da, sizeof(a)));
    CUDA_CHECK(cudaMalloc(&db, sizeof(b)));
    CUDA_CHECK(cudaMalloc(&dc, sizeof(c)));
    CUDA_CHECK(cudaMemcpy(da, a, sizeof(a), cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(db, b, sizeof(b), cudaMemcpyHostToDevice));
    vector_add<<<(n + 127)/128, 128>>>(da, db, dc, n);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
    CUDA_CHECK(cudaMemcpy(c, dc, sizeof(c), cudaMemcpyDeviceToHost));
    bool valid = true;
    for (int i = 0; i < n; ++i) if (std::abs(c[i] - (a[i] + b[i])) > 1e-12) valid = false;
    CUDA_CHECK(cudaFree(da)); CUDA_CHECK(cudaFree(db)); CUDA_CHECK(cudaFree(dc));
    return valid ? 0 : 1;
}
