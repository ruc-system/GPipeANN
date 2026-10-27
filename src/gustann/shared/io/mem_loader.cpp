#include "loader.hpp"
#include "../../../shared/io/file_loader_base.hpp"

namespace shared {
namespace {
using Base = quiver_debug::FileLoaderBase<IndexLoader, IoRequest, DirectIoRequest>;
class FileLoader final : public Base {
 public:
  using Base::Base;
  void submit_traced_task(const std::vector<TracedIoRequest>& requests, int, int) override {
    for (const auto& request : requests) {
      const int index = request.trace_index;
      if (index >= 0) {
        const int64_t started = now_ns();
        if (request.enqueue_ns) request.enqueue_ns[index] = started;
        if (request.submit_ns) request.submit_ns[index] = started;
      }
      read_block(request.block_id, request.dest);
      if (index >= 0 && request.complete_ns) request.complete_ns[index] = now_ns();
    }
  }
};
}  // namespace

std::shared_ptr<IndexLoader> create_mem_loader_sync(
    const char* filename, int64_t num_pages, int64_t io_bytes) {
  return std::make_shared<FileLoader>(filename, num_pages, io_bytes);
}

}  // namespace shared
