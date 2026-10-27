#pragma once

#include <cstdint>

namespace shared {

inline constexpr int64_t SECTOR_LEN = 4096;

struct Layout {
  int64_t num_dims;
  int64_t max_m0;
  int64_t enter_point;

  int64_t data_size;
  int64_t node_size;

  int64_t num_pages;
  int64_t num_data;

  int64_t nodes_per_page = 1;
  int64_t sectors_per_node = 1;
  int64_t io_bytes = SECTOR_LEN;
};

inline int node_first_page(int node_id, int nodes_per_page,
                           int sectors_per_node) {
  const int npp = nodes_per_page > 0 ? nodes_per_page : 1;
  const int spn = sectors_per_node > 0 ? sectors_per_node : 1;
  return (node_id / npp) * spn;
}

}  // namespace shared
