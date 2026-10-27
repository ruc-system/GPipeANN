#pragma once

#include <cerrno>
#include <cstdint>
#include <cstdlib>

namespace shared {

inline constexpr int64_t kSectorBytes = 4096;

// Map a 4KB-indexed first page onto (ssd, LBA). Multi-sector nodes stripe by
// node so both sectors stay consecutive on one SSD: 4KB packed pages keep
// ssd=page%n, off=base+page/n.
inline void map_index_page_to_ssd(long first_page, long io_bytes, int num_ssd,
                                  long base_lba, long block_offset, int* ssd,
                                  long* off) {
  const long logical = first_page + block_offset;
  // Preserve the original 4KB hot path exactly. This function is called for
  // every SSD request, so avoid the extra divisions for existing indexes.
  if (io_bytes == kSectorBytes) {
    *ssd = static_cast<int>(logical % num_ssd);
    *off = base_lba + logical / num_ssd;
    return;
  }
  long sectors = io_bytes / kSectorBytes;
  if (sectors < 1) {
    sectors = 1;
  }
  const long stripe_key = logical / sectors;
  *ssd = static_cast<int>(stripe_key % num_ssd);
  *off = base_lba + (stripe_key / num_ssd) * sectors;
}

inline long spdk_base_lba_from_env() {
  const char* env = std::getenv("SPDK_BASE_LBA");
  if (env == nullptr || *env == '\0') {
    return 0;
  }

  errno = 0;
  char* end = nullptr;
  const long value = std::strtol(env, &end, 10);
  if (errno != 0 || end == env || *end != '\0' || value < 0) {
    return 0;
  }
  return value;
}

inline long spdk_block_offset_from_env() {
  const char* env = std::getenv("QUIVER_SPDK_BLOCK_OFFSET");
  if (env == nullptr || *env == '\0') {
    return 0;
  }

  errno = 0;
  char* end = nullptr;
  const long value = std::strtol(env, &end, 10);
  if (errno != 0 || end == env || *end != '\0' || value < 0) {
    return 0;
  }
  return value;
}

}  // namespace shared
