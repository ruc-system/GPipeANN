#include "loader.hpp"
#include "../../../shared/io/file_loader_base.hpp"

namespace shared {
namespace {
using Base = gpipeann_debug::FileLoaderBase<IndexLoader, IoRequest, DirectIoRequest>;
class FileLoader final : public Base {
 public:
  using Base::Base;
#ifdef FLASHANNS_LATENCY_PROBE
  void submit_traced_task(const std::vector<TracedIoRequest>& requests, int, int) override {
    for (const auto& request : requests) {
      read_block(request.block_id, request.dest);
      if (request.complete_ns)
        __atomic_store_n(request.complete_ns, now_ns(), __ATOMIC_RELEASE);
    }
  }
#endif
};
}  // namespace

std::shared_ptr<IndexLoader> create_mem_loader_sync(
    const char* filename, int64_t num_pages, int64_t io_bytes) {
  return std::make_shared<FileLoader>(filename, num_pages, io_bytes);
}

}  // namespace shared
