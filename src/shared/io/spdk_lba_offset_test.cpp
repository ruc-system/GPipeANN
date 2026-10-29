#include "shared/io/spdk_lba_offset.hpp"

#include <cstdlib>
#include <iostream>

namespace {

void require(bool condition, const char* message) {
  if (!condition) {
    std::cerr << "spdk_lba_offset_test failed: " << message << std::endl;
    std::exit(1);
  }
}

}  // namespace

int main() {
  unsetenv("SPDK_BASE_LBA");
  require(shared::spdk_base_lba_from_env() == 0,
          "SPDK_BASE_LBA should default to zero");

  setenv("SPDK_BASE_LBA", "436207616", 1);
  require(shared::spdk_base_lba_from_env() == 436207616,
          "SPDK_BASE_LBA should parse a non-zero 4KB-block offset");

  setenv("SPDK_BASE_LBA", "", 1);
  require(shared::spdk_base_lba_from_env() == 0,
          "empty SPDK_BASE_LBA should behave like unset");

  setenv("SPDK_BASE_LBA", "abc", 1);
  require(shared::spdk_base_lba_from_env() == 0,
          "invalid SPDK_BASE_LBA should fall back to zero");

  unsetenv("SPDK_BASE_LBA");
  unsetenv("GPIPEANN_SPDK_BLOCK_OFFSET");
  require(shared::spdk_block_offset_from_env() == 0,
          "GPIPEANN_SPDK_BLOCK_OFFSET should default to zero");

  setenv("GPIPEANN_SPDK_BLOCK_OFFSET", "1", 1);
  require(shared::spdk_block_offset_from_env() == 1,
          "GPIPEANN_SPDK_BLOCK_OFFSET should parse a one-page offset");

  setenv("GPIPEANN_SPDK_BLOCK_OFFSET", "", 1);
  require(shared::spdk_block_offset_from_env() == 0,
          "empty GPIPEANN_SPDK_BLOCK_OFFSET should behave like unset");

  setenv("GPIPEANN_SPDK_BLOCK_OFFSET", "-1", 1);
  require(shared::spdk_block_offset_from_env() == 0,
          "negative GPIPEANN_SPDK_BLOCK_OFFSET should fall back to zero");

  unsetenv("GPIPEANN_SPDK_BLOCK_OFFSET");

  int ssd = -1;
  long off = -1;
  shared::map_index_page_to_ssd(0, 4096, 4, 100, 0, &ssd, &off);
  require(ssd == 0 && off == 100, "4KB page 0 mapping");
  shared::map_index_page_to_ssd(5, 4096, 4, 100, 0, &ssd, &off);
  require(ssd == 1 && off == 101, "4KB page 5 mapping");

  shared::map_index_page_to_ssd(0, 8192, 4, 100, 0, &ssd, &off);
  require(ssd == 0 && off == 100, "8KB node 0 mapping");
  shared::map_index_page_to_ssd(2, 8192, 4, 100, 0, &ssd, &off);
  require(ssd == 1 && off == 100, "8KB node 1 mapping");
  shared::map_index_page_to_ssd(8, 8192, 4, 100, 0, &ssd, &off);
  require(ssd == 0 && off == 102, "8KB node 4 mapping");

  return 0;
}
