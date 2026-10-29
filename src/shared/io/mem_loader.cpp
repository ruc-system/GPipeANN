#include "loader.hpp"
#include "file_loader_base.hpp"

namespace shared {
namespace {
using Base = gpipeann_debug::FileLoaderBase<IndexLoader, IoRequest, DirectIoRequest>;
using FileLoader = Base;
}  // namespace

std::shared_ptr<IndexLoader> create_mem_loader_sync(
    const char* filename, int64_t num_pages, int64_t io_bytes) {
  return std::make_shared<FileLoader>(filename, num_pages, io_bytes);
}

}  // namespace shared
