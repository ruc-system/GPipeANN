#pragma once

#include "file_loader_base.hpp"

#include <algorithm>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <thread>

namespace {
void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

template <class Callable>
void expect_error(Callable function) {
  bool failed = false;
  try { function(); } catch (const std::exception&) { failed = true; }
  require(failed, "invalid request/index should fail");
}

void expect_pages(const uint8_t* data, int first, int count) {
  for (int page = 0; page < count; ++page)
    for (int byte = 0; byte < shared::PAGE_SIZE; ++byte)
      require(data[page * shared::PAGE_SIZE + byte] == 0x40 + first + page,
              "wrong block offset, size, or contents");
}

template <class Request>
void check_direct(shared::IndexLoader& loader) {
  std::vector<uint8_t> data(shared::PAGE_SIZE, 0);
  volatile int32_t status = 0;
  volatile int64_t completed = 0;
  Request request{5, data.data(), &status, 7};
  if constexpr (gpipeann_debug::HasCompletionTime<Request>::value)
    request.complete_ns = &completed;
  loader.submit_direct({request}, 0);
  require(__atomic_load_n(&status, __ATOMIC_ACQUIRE) == 7, "completion not published");
  expect_pages(data.data(), 5, 1);
  if constexpr (gpipeann_debug::HasCompletionTime<Request>::value)
    require(__atomic_load_n(&completed, __ATOMIC_ACQUIRE) > 0, "missing completion time");
}

void run_file_loader_test(const std::filesystem::path& path) {
  auto loader = shared::create_mem_loader_sync(path.c_str(), 6);
  std::vector<uint8_t> first(shared::PAGE_SIZE), last(shared::PAGE_SIZE);
  loader->submit_task({{5, last.data()}, {0, first.data()}}, 0, 3);
  require(loader->poll_task(3), "synchronous requests must complete");
  expect_pages(first.data(), 0, 1);
  expect_pages(last.data(), 5, 1);
  check_direct<shared::DirectIoRequest>(*loader);
  auto stats = loader->snapshot_stats();
  require(stats.pages_completed == 3 && stats.counts_closed(), "incorrect I/O counts");
  loader->clear_stats();
  require(loader->snapshot_stats().pages_completed == 0, "clear_stats failed");

  std::vector<std::thread> readers;
  for (int thread = 0; thread < 4; ++thread) {
    readers.emplace_back([&, thread] {
      std::vector<uint8_t> data(shared::PAGE_SIZE);
      for (int i = 0; i < 12; ++i) {
        int page = (i + thread) % 6;
        loader->submit_task({{page, data.data()}}, thread, thread);
        expect_pages(data.data(), page, 1);
      }
    });
  }
  for (auto& reader : readers) reader.join();
  require(loader->snapshot_stats().pages_completed == 48, "concurrent reads lost");
  // The debug backend observes file writes instead of keeping a separate copy.
  {
    std::fstream output(path, std::ios::in | std::ios::out | std::ios::binary);
    output.seekp(3 * shared::PAGE_SIZE);
    output.put(static_cast<char>(0x7f));
    output.flush();
    require(output.good(), "cannot update debug index fixture");
  }
  loader->submit_task({{2, first.data()}}, 0, 0);
  require(first[0] == 0x7f && first[1] == 0x42, "debug reads used a stale index copy");
  auto wide = shared::create_mem_loader_sync(path.c_str(), 6, 2 * shared::PAGE_SIZE);
  uint8_t* data = wide->create_buffer(2 * shared::PAGE_SIZE);
  wide->submit_task({{4, data}}, 0, 0);
  expect_pages(data, 4, 2);
  expect_error([&] { wide->submit_task({{5, data}}, 0, 0); });
  expect_error([&] { wide->submit_task({{-1, data}}, 0, 0); });
  expect_error([&] { wide->submit_task({{0, nullptr}}, 0, 0); });
  wide->destroy_buffer(data);
  expect_error([&] { loader->create_buffer(0); });
  expect_error([&] { shared::create_mem_loader_sync(path.c_str(), 0); });
  expect_error([&] { shared::create_mem_loader_sync(path.c_str(), 7); });
  expect_error([&] { shared::create_mem_loader_sync(path.c_str(), 6, 4097); });
  expect_error([&] { shared::create_mem_loader_sync("/nonexistent/gpipeann-index", 6); });

#ifdef GPIPEANN_FILE_TEST_GUSTANN_TRACE
  int64_t enqueued[1] = {0}, submitted[1] = {0}, completed[1] = {0};
  shared::TracedIoRequest traced{1, first.data(), 0, enqueued, submitted, completed};
  loader->submit_traced_task({traced}, 0, 0);
  expect_pages(first.data(), 1, 1);
  require(enqueued[0] > 0 && submitted[0] >= enqueued[0] && completed[0] >= submitted[0],
          "missing or unordered GustANN trace timestamps");
#endif
#ifdef FLASHANNS_LATENCY_PROBE
  volatile int64_t completed = 0;
  shared::TracedIoRequest traced{1, first.data(), 0, &completed};
  loader->submit_traced_task({traced}, 0, 0);
  expect_pages(first.data(), 1, 1);
  require(__atomic_load_n(&completed, __ATOMIC_ACQUIRE) > 0, "missing FlashANNS trace time");
#endif

  // A file truncated after opening must report an error, not publish success.
  std::filesystem::resize_file(path, shared::PAGE_SIZE);
  volatile int32_t status = 0;
  shared::DirectIoRequest invalid{0, first.data(), &status, 7};
  expect_error([&] { loader->submit_direct({invalid}, 0); });
  require(__atomic_load_n(&status, __ATOMIC_ACQUIRE) == 0, "failed read published success");
}
}  // namespace

int main() {
  char name[] = "/tmp/gpipeann-file-loader-XXXXXX";
  char* directory = ::mkdtemp(name);
  if (!directory) return 1;
  const auto path = std::filesystem::path(directory) / "disk.index";
  try {
    {
      std::ofstream output(path, std::ios::binary);
      std::vector<uint8_t> page(shared::PAGE_SIZE, 0xaa);
      output.write(reinterpret_cast<const char*>(page.data()), page.size());
      for (int i = 0; i < 6; ++i) {
        std::fill(page.begin(), page.end(), static_cast<uint8_t>(0x40 + i));
        output.write(reinterpret_cast<const char*>(page.data()), page.size());
      }
      require(output.good(), "cannot write index fixture");
    }
    run_file_loader_test(path);
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    std::filesystem::remove_all(directory);
    return 1;
  }
  std::filesystem::remove_all(directory);
  return 0;
}
