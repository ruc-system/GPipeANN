#pragma once

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <string>

#include "shared/common/data_type.hpp"
#include "shared/common/layout.hpp"
#include "shared/common/logging.hpp"

namespace bin_common {

inline void parse_diskann_metadata(const std::string& fpath,
                                   shared::Layout& layout,
                                   shared::DataType data_type) {
  const size_t data_size =
      data_type == shared::FLOAT ? sizeof(float) : sizeof(int8_t);

  std::ifstream input(fpath, std::ios::binary);
  if (!input.is_open()) {
    ERROR("Failed to open file {}", fpath);
    std::exit(-1);
  }
  INFO("load DiskANN index from {}", fpath);

  uint32_t nr = 0;
  uint32_t nc = 0;
  input.read(reinterpret_cast<char*>(&nr), sizeof(uint32_t));
  input.read(reinterpret_cast<char*>(&nc), sizeof(uint32_t));
  (void)nr;
  (void)nc;

  uint64_t disk_nnodes = 0;
  uint64_t disk_ndims = 0;
  input.read(reinterpret_cast<char*>(&disk_nnodes), sizeof(uint64_t));
  input.read(reinterpret_cast<char*>(&disk_ndims), sizeof(uint64_t));
  layout.num_data = disk_nnodes;
  layout.num_dims = disk_ndims;

  uint64_t medoid_id = 0;
  uint64_t max_node_len = 0;
  uint64_t nnodes_per_sector = 0;
  input.read(reinterpret_cast<char*>(&medoid_id), sizeof(uint64_t));
  input.read(reinterpret_cast<char*>(&max_node_len), sizeof(uint64_t));
  input.read(reinterpret_cast<char*>(&nnodes_per_sector), sizeof(uint64_t));
  if (!input || disk_nnodes == 0 || disk_ndims == 0 || max_node_len == 0 ||
      medoid_id >= disk_nnodes) {
    ERROR("Invalid or truncated DiskANN metadata in '{}'", fpath);
    std::exit(-1);
  }
  layout.enter_point = medoid_id;
  // disk_ndims is the full vector dim when the SSD node stores uncompressed
  // coordinates, or the PQ byte width when DiskANN used --PQ_disk_bytes.
  const uint64_t uncompressed_bytes = disk_ndims * data_size;
  if (max_node_len >= uncompressed_bytes + 2 * sizeof(uint32_t)) {
    layout.data_size = static_cast<int64_t>(uncompressed_bytes);
  } else {
    layout.data_size = static_cast<int64_t>(disk_ndims);
  }
  if (max_node_len < static_cast<uint64_t>(layout.data_size) +
                         2 * sizeof(uint32_t) ||
      (max_node_len - static_cast<uint64_t>(layout.data_size)) %
              sizeof(uint32_t) !=
          0) {
    ERROR("Index '{}' has inconsistent node layout: max_node_len={}, "
          "data_size={}",
          fpath, max_node_len, layout.data_size);
    std::exit(-1);
  }
  layout.max_m0 =
      ((max_node_len - static_cast<uint64_t>(layout.data_size)) /
       sizeof(uint32_t)) -
      1;

  uint64_t num_frozen = 0;
  uint64_t file_frozen_id = 0;
  uint64_t reorder_exists = 0;
  input.read(reinterpret_cast<char*>(&num_frozen), sizeof(uint64_t));
  input.read(reinterpret_cast<char*>(&file_frozen_id), sizeof(uint64_t));
  input.read(reinterpret_cast<char*>(&reorder_exists), sizeof(uint64_t));
  (void)num_frozen;
  (void)file_frozen_id;
  (void)reorder_exists;

  layout.node_size = static_cast<int64_t>(max_node_len);
  if (nnodes_per_sector > 0) {
    if (max_node_len > shared::SECTOR_LEN ||
        max_node_len * nnodes_per_sector > shared::SECTOR_LEN) {
      ERROR("Index '{}' has invalid packed layout: max_node_len={}, "
            "nnodes_per_sector={}",
            fpath, max_node_len, nnodes_per_sector);
      std::exit(-1);
    }
    layout.nodes_per_page = static_cast<int64_t>(nnodes_per_sector);
    layout.sectors_per_node = 1;
  } else {
    if (max_node_len == 0) {
      ERROR("Index '{}' has max_node_len=0 with nnodes_per_sector=0", fpath);
      std::exit(-1);
    }
    const uint64_t sectors =
        (max_node_len + shared::SECTOR_LEN - 1) / shared::SECTOR_LEN;
    if (sectors < 1 || sectors > 8) {
      ERROR("Index '{}' multi-sector node uses {} sectors (max_node_len={}); "
            "supported range is 1..8",
            fpath, sectors, max_node_len);
      std::exit(-1);
    }
    layout.nodes_per_page = 1;
    layout.sectors_per_node = static_cast<int64_t>(sectors);
  }
  layout.io_bytes = layout.sectors_per_node * shared::SECTOR_LEN;
  layout.num_pages =
      ((layout.num_data + layout.nodes_per_page - 1) / layout.nodes_per_page) *
      layout.sectors_per_node;

  INFO("num_data={}, num_dims(disk)={}, max_m0={}, enter_point={}, node_size={}, "
       "data_size={}, nodes_per_page={}, sectors_per_node={}, io_bytes={}",
       layout.num_data, disk_ndims, layout.max_m0, layout.enter_point,
       layout.node_size, layout.data_size, layout.nodes_per_page,
       layout.sectors_per_node, layout.io_bytes);
}

}  // namespace bin_common
