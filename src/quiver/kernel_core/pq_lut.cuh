#pragma once

#include "../../shared/index/pq_device.cuh"

namespace quiver {

// All CTA threads must participate. The caller provides the LUT for its slot;
// unlike PQSearchData::init_query, no blockIdx-based addressing is assumed.
__device__ __forceinline__ void init_slot_pq_lut(
    shared::PQSearchData* pqd, float* qdata, float* dist_vec)
{
    const int tid = threadIdx.x;
    const int num_pivots = shared::PQSearchData::num_pivots;
    const int num_chunks = pqd->num_chunks;
    const int dim = pqd->dim;
    // The high-dimensional path applies to every 1536-D PQ layout. Chunk
    // boundaries come from the index rather than assuming PQ64/equal chunks.
    for (int i = tid; i < dim; i += blockDim.x)
        qdata[i] -= pqd->centroid[i];
    __syncthreads();
    if (dim == 1536) {
        // A lane owns a (chunk, pivot) output. Accumulate in original dimension
        // order in a register, replacing per-dimension global RMW and barriers.
        for (int output = tid; output < num_chunks * num_pivots;
             output += blockDim.x) {
            const int chunk = output / num_pivots;
            const int pivot = output % num_pivots;
            const int begin = pqd->chunk_offsets[chunk];
            const int end = pqd->chunk_offsets[chunk + 1];
            float sum = 0;
            for (int i = begin; i < end; ++i) {
                float dd = qdata[i] - pqd->pivots_t[i * num_pivots + pivot];
                sum += dd * dd;
            }
            dist_vec[output] = sum;
        }
    } else {
        for (size_t i = tid; i < (size_t)num_pivots * num_chunks; i += blockDim.x)
            dist_vec[i] = 0;
        __syncthreads();
        for (int i = 0; i < dim; ++i) {
            int idx = pqd->chunk_id[i];
            for (int j = tid; j < num_pivots; j += blockDim.x) {
                float dd = qdata[i] - pqd->pivots_t[i * num_pivots + j];
                dist_vec[idx * num_pivots + j] += dd * dd;
            }
            __syncthreads();
        }
    }
    __syncthreads();
    for (int i = tid; i < dim; i += blockDim.x)
        qdata[i] += pqd->centroid[i];
}

} // namespace quiver
