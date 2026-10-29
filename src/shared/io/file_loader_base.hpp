#pragma once

#include <atomic>
#include <cerrno>
#include <chrono>
#include <cstdint>
#include <fcntl.h>
#include <limits>
#include <stdexcept>
#include <system_error>
#include <type_traits>
#include <utility>
#include <vector>
#include <sys/stat.h>
#include <unistd.h>

namespace gpipeann_debug {

template <class Request, class = void>
struct HasCompletionTime : std::false_type {};
template <class Request>
struct HasCompletionTime<Request, std::void_t<decltype(std::declval<Request>().complete_ns)>>
    : std::true_type {};

// A synchronous block device backed by an ordinary index file. It implements
// the existing loader contract; search kernels, polling, and buffers are shared
// with the SSD path. All three systems use this one host-side implementation.
template <class Interface, class TaskRequest, class DirectRequest>
class FileLoaderBase : public Interface {
  static constexpr int64_t kPageBytes = 4096;
  int fd_ = -1;
  int64_t num_pages_;
  int64_t io_bytes_;
  std::atomic<uint64_t> submitted_{0};
  std::atomic<uint64_t> completed_{0};

 protected:
  static int64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
  }

  void read_block(int first_page, void* destination) {
    if (!destination || first_page < 0 ||
        first_page > num_pages_ - io_bytes_ / kPageBytes)
      throw std::out_of_range("File loader request is outside the index");
    submitted_.fetch_add(1, std::memory_order_relaxed);
    const off_t offset = (static_cast<int64_t>(first_page) + 1) * kPageBytes;
    int64_t done = 0;
    while (done < io_bytes_) {
      const ssize_t bytes = ::pread(fd_, static_cast<uint8_t*>(destination) + done,
                                    static_cast<size_t>(io_bytes_ - done), offset + done);
      if (bytes < 0) {
        if (errno == EINTR) continue;
        throw std::system_error(errno, std::generic_category(), "Read debug index");
      }
      if (bytes == 0) throw std::runtime_error("Unexpected EOF in debug index");
      done += bytes;
    }
    completed_.fetch_add(1, std::memory_order_relaxed);
  }

 public:
  FileLoaderBase(const char* filename, int64_t num_pages, int64_t io_bytes)
      : num_pages_(num_pages), io_bytes_(io_bytes) {
    if (num_pages <= 0 ||
        num_pages > std::numeric_limits<int64_t>::max() / kPageBytes - 1 ||
        io_bytes <= 0 || io_bytes % kPageBytes != 0 || io_bytes / kPageBytes > num_pages)
      throw std::invalid_argument("Invalid debug index page count or I/O size");
    fd_ = ::open(filename, O_RDONLY | O_CLOEXEC);
    if (fd_ < 0)
      throw std::system_error(errno, std::generic_category(), "Open debug index");
    try {
      struct stat info {};
      if (::fstat(fd_, &info) != 0)
        throw std::system_error(errno, std::generic_category(), "Stat debug index");
      if (!S_ISREG(info.st_mode) || info.st_size < (num_pages + 1) * kPageBytes)
        throw std::runtime_error("Debug index is not a complete regular index file");
    } catch (...) {
      ::close(fd_);
      throw;
    }
  }

  FileLoaderBase(const FileLoaderBase&) = delete;
  FileLoaderBase& operator=(const FileLoaderBase&) = delete;
  ~FileLoaderBase() override { ::close(fd_); }

  void submit_task(const std::vector<TaskRequest>& requests, int, int) override {
    for (const auto& request : requests) read_block(request.first, request.second);
  }

  void submit_direct(const std::vector<DirectRequest>& requests, int) override {
    for (const auto& request : requests) {
      read_block(request.block_id, request.dest);
      if constexpr (HasCompletionTime<DirectRequest>::value) {
        if (request.complete_ns)
          __atomic_store_n(request.complete_ns, now_ns(), __ATOMIC_RELEASE);
      }
      // Publish completion only after the full read and optional timestamp.
      if (request.status_ptr)
        __atomic_store_n(request.status_ptr, request.done_value, __ATOMIC_RELEASE);
    }
  }

  bool poll_task(int) override { return true; }
  uint8_t* create_buffer(int64_t size) override {
    if (size <= 0) throw std::invalid_argument("Invalid debug I/O buffer size");
    return new uint8_t[static_cast<size_t>(size)];
  }
  void destroy_buffer(uint8_t* buffer) override { delete[] buffer; }

  using Stats = decltype(std::declval<Interface>().snapshot_stats());
  Stats snapshot_stats() const override {
    Stats stats;
    stats.pages_enqueued = stats.pages_submitted = submitted_.load(std::memory_order_relaxed);
    stats.pages_completed = completed_.load(std::memory_order_relaxed);
    stats.per_ssd_submitted = {stats.pages_submitted};
    stats.per_ssd_completed = {stats.pages_completed};
    return stats;
  }
  void clear_stats() override {
    submitted_.store(0, std::memory_order_relaxed);
    completed_.store(0, std::memory_order_relaxed);
  }
};

}  // namespace gpipeann_debug
