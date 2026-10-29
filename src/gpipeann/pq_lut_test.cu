#include "kernel_core/pq_lut.cuh"

#include <cstdio>
#include <cstring>
#include <random>
#include <vector>

__global__ void reference_lut(shared::PQSearchData p, float* queries) {
    p.init_query(queries + (size_t)blockIdx.x * p.dim);
}

__global__ void optimized_lut(shared::PQSearchData p, float* queries) {
    gpipeann::init_slot_pq_lut(&p, queries + (size_t)blockIdx.x * p.dim,
        p.pq_dists + (size_t)blockIdx.x * p.num_chunks * p.num_pivots);
}

template <class T> T* upload(const std::vector<T>& values) {
    T* ptr = nullptr;
    CHECK_CUDA(cudaMalloc(&ptr, values.size() * sizeof(T)));
    CHECK_CUDA(cudaMemcpy(ptr, values.data(), values.size() * sizeof(T), cudaMemcpyHostToDevice));
    return ptr;
}

bool run_case(int dim, int chunks, bool uneven, unsigned seed) {
    constexpr int queries = 8;
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> distribution(-1.0f, 1.0f);
    std::vector<float> q(dim * queries), centroid(dim), pivots(dim * 256);
    for (auto* v : {&q, &centroid, &pivots})
        for (float& x : *v) x = distribution(rng);
    std::vector<int> offsets(chunks + 1), ids(dim);
    for (int chunk = 0; chunk <= chunks; ++chunk)
        offsets[chunk] = chunk * dim / chunks;
    if (uneven && chunks > 1 && offsets[1] + 1 < offsets[2])
        ++offsets[1];
    for (int chunk = 0; chunk < chunks; ++chunk)
        for (int i = offsets[chunk]; i < offsets[chunk + 1]; ++i)
            ids[i] = chunk;
    shared::PQSearchData p;
    p.dim = dim;
    p.num_chunks = chunks;
    p.centroid = upload(centroid);
    p.pivots_t = upload(pivots);
    p.chunk_id = upload(ids);
    p.chunk_offsets = upload(offsets);
    float *qref = upload(q), *qopt = upload(q);
    std::vector<float> ref(queries * chunks * 256), opt(ref.size());
    float *lutref = upload(ref), *lutopt = upload(opt);
    p.pq_dists = lutref;
    reference_lut<<<queries, 128>>>(p, qref);
    CHECK_CUDA(cudaGetLastError());
    p.pq_dists = lutopt;
    optimized_lut<<<queries, 128>>>(p, qopt);
    CHECK_CUDA(cudaGetLastError());
    CHECK_CUDA(cudaDeviceSynchronize());
    CHECK_CUDA(cudaMemcpy(ref.data(), lutref, ref.size() * sizeof(float), cudaMemcpyDeviceToHost));
    CHECK_CUDA(cudaMemcpy(opt.data(), lutopt, opt.size() * sizeof(float), cudaMemcpyDeviceToHost));
    size_t mismatches = 0;
    for (size_t i = 0; i < ref.size(); ++i)
        mismatches += std::memcmp(&ref[i], &opt[i], sizeof(float)) != 0;
    std::vector<float> qr(q.size()), qo(q.size());
    CHECK_CUDA(cudaMemcpy(qr.data(), qref, qr.size() * sizeof(float), cudaMemcpyDeviceToHost));
    CHECK_CUDA(cudaMemcpy(qo.data(), qopt, qo.size() * sizeof(float), cudaMemcpyDeviceToHost));
    bool restored = std::memcmp(qr.data(), qo.data(), qr.size() * sizeof(float)) == 0;
    std::printf("dim=%d chunks=%d uneven=%d seed=%u LUT_bit_mismatches=%zu query_equal=%d\n",
                dim, chunks, uneven, seed, mismatches, restored);
    for (void* ptr : {static_cast<void*>(p.centroid), static_cast<void*>(p.pivots_t),
                     static_cast<void*>(p.chunk_id), static_cast<void*>(qref),
                     static_cast<void*>(p.chunk_offsets),
                     static_cast<void*>(qopt), static_cast<void*>(lutref), static_cast<void*>(lutopt)})
        CHECK_CUDA(cudaFree(ptr));
    return mismatches == 0 && restored;
}

int main() {
    bool ok = true;
    for (unsigned seed : {1u, 7u, 42u}) {
        ok &= run_case(1536, 64, false, seed);
        ok &= run_case(1536, 64, true, seed);
        ok &= run_case(1536, 32, false, seed);
        ok &= run_case(1536, 32, true, seed);
        ok &= run_case(1536, 96, true, seed);
        ok &= run_case(1536, 192, true, seed);
        ok &= run_case(128, 32, false, seed);
    }
    return ok ? 0 : 1;
}
