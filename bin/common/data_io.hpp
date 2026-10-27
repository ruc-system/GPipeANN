#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#include "shared/common/logging.hpp"

namespace bin_common {

struct QueryData {
  std::unique_ptr<float[]> values;
  size_t dims = 0;
  size_t count = 0;
};

struct GroundTruthData {
  std::unique_ptr<int[]> values;
  size_t width = 0;
  size_t count = 0;
};

template <class T>
inline std::unique_ptr<T[]> read_typed_bin(const std::string& fname,
                                           size_t& d_out,
                                           size_t& n_out) {
  std::ifstream input(fname, std::ios::binary);
  if (!input.is_open()) {
    ERROR("Failed to open file {}", fname);
    std::exit(1);
  }

  int32_t npts = 0;
  int32_t ndims = 0;
  input.read(reinterpret_cast<char*>(&npts), sizeof(int32_t));
  input.read(reinterpret_cast<char*>(&ndims), sizeof(int32_t));

  d_out = static_cast<size_t>(ndims);
  n_out = static_cast<size_t>(npts);

  auto result = std::make_unique<T[]>(d_out * n_out);
  input.read(reinterpret_cast<char*>(result.get()),
             sizeof(T) * d_out * n_out);
  return result;
}

inline std::vector<std::string> read_ssd_list(const std::string& ssd_list_file) {
  std::vector<std::string> ssd_lists;
  if (ssd_list_file.empty()) {
    return ssd_lists;
  }

  std::ifstream input(ssd_list_file);
  if (!input.is_open()) {
    ERROR("Failed to open SSD list file {}", ssd_list_file);
    std::exit(1);
  }

  std::string line;
  while (input >> line) {
    INFO("USE SSD: \"{}\"", line);
    ssd_lists.push_back(line);
  }
  return ssd_lists;
}

inline QueryData load_queries_as_float(const std::string& query_file,
                                       int repeat = 1) {
  QueryData queries;

  if (query_file.find(".u8bin") != std::string::npos) {
    auto raw = read_typed_bin<uint8_t>(query_file, queries.dims, queries.count);
    queries.values = std::make_unique<float[]>(queries.dims * queries.count);
    std::copy(raw.get(), raw.get() + queries.dims * queries.count,
              queries.values.get());
  } else if (query_file.find(".i8bin") != std::string::npos) {
    auto raw = read_typed_bin<int8_t>(query_file, queries.dims, queries.count);
    queries.values = std::make_unique<float[]>(queries.dims * queries.count);
    std::copy(raw.get(), raw.get() + queries.dims * queries.count,
              queries.values.get());
  } else {
    queries.values = read_typed_bin<float>(query_file, queries.dims,
                                           queries.count);
  }

  INFO("Read {} queries", queries.count);

  if (repeat > 1) {
    const size_t original_count = queries.count;
    auto repeated =
        std::make_unique<float[]>(queries.dims * original_count * repeat);
    for (int i = 0; i < repeat; ++i) {
      std::copy(queries.values.get(),
                queries.values.get() + queries.dims * original_count,
                repeated.get() + i * queries.dims * original_count);
    }
    queries.values = std::move(repeated);
    queries.count = original_count * static_cast<size_t>(repeat);
  }

  return queries;
}

inline GroundTruthData load_ground_truth(const std::string& gt_file) {
  GroundTruthData gt;
  gt.values = read_typed_bin<int>(gt_file, gt.width, gt.count);
  return gt;
}

inline std::vector<int> load_query_ef_csv(const std::string& path,
                                          size_t unique_count, int repeat) {
  if (path.empty() || unique_count == 0) {
    return {};
  }
  std::ifstream input(path);
  if (!input.is_open()) {
    throw std::runtime_error("Failed to open query-ef CSV " + path);
  }

  auto trim = [](std::string value) {
    const size_t first = value.find_first_not_of(" \t\r");
    if (first == std::string::npos) return std::string{};
    const size_t last = value.find_last_not_of(" \t\r");
    return value.substr(first, last - first + 1);
  };

  std::string header;
  if (!std::getline(input, header)) {
    throw std::runtime_error("Empty query-ef CSV " + path);
  }
  int ef_col = -1;
  int id_col = -1;
  {
    std::stringstream stream(header);
    std::string column;
    int index = 0;
    while (std::getline(stream, column, ',')) {
      column = trim(column);
      if (column == "ef_search" || column == "ef") ef_col = index;
      if (column == "query_id") id_col = index;
      ++index;
    }
  }
  if (ef_col < 0) {
    throw std::runtime_error("query-ef CSV needs an ef_search column: " +
                             path);
  }

  std::vector<int> unique(unique_count, -1);
  std::string line;
  size_t row = 0;
  while (std::getline(input, line)) {
    if (trim(line).empty()) continue;
    std::stringstream stream(line);
    std::string cell;
    std::vector<std::string> cells;
    while (std::getline(stream, cell, ',')) cells.push_back(trim(cell));
    if (ef_col >= static_cast<int>(cells.size())) {
      throw std::runtime_error("Missing ef value in query-ef CSV row " +
                               std::to_string(row + 2));
    }
    const long long parsed_qid =
        id_col >= 0 && id_col < static_cast<int>(cells.size())
            ? std::stoll(cells[id_col])
            : static_cast<long long>(row);
    if (parsed_qid < 0 ||
        static_cast<size_t>(parsed_qid) >= unique_count) {
      throw std::runtime_error("query_id out of range in query-ef CSV row " +
                               std::to_string(row + 2));
    }
    const size_t qid = static_cast<size_t>(parsed_qid);
    if (unique[qid] != -1) {
      throw std::runtime_error("Duplicate query_id in query-ef CSV: " +
                               std::to_string(qid));
    }
    const int ef = std::stoi(cells[ef_col]);
    if (ef < 1) {
      throw std::runtime_error("ef_search must be positive for query_id " +
                               std::to_string(qid));
    }
    unique[qid] = ef;
    ++row;
  }
  for (size_t qid = 0; qid < unique_count; ++qid) {
    if (unique[qid] < 1) {
      throw std::runtime_error("Missing ef for query_id " +
                               std::to_string(qid) + " in " + path);
    }
  }

  const int reps = std::max(repeat, 1);
  std::vector<int> result(unique_count * static_cast<size_t>(reps));
  for (int r = 0; r < reps; ++r) {
    std::copy(unique.begin(), unique.end(),
              result.begin() + static_cast<size_t>(r) * unique_count);
  }
  return result;
}

template <class T>
inline void write_typed_bin(const std::string& path, const T* values,
                            size_t count, size_t dims) {
  if (count > static_cast<size_t>(INT32_MAX) ||
      dims > static_cast<size_t>(INT32_MAX)) {
    throw std::runtime_error("Binary result dimensions exceed int32 range");
  }

  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  if (!output.is_open()) {
    throw std::runtime_error("Failed to open binary result file " + path);
  }

  const int32_t count_header = static_cast<int32_t>(count);
  const int32_t dims_header = static_cast<int32_t>(dims);
  output.write(reinterpret_cast<const char*>(&count_header),
               sizeof(count_header));
  output.write(reinterpret_cast<const char*>(&dims_header),
               sizeof(dims_header));
  output.write(reinterpret_cast<const char*>(values),
               sizeof(T) * count * dims);
  if (!output) {
    throw std::runtime_error("Failed to write binary result file " + path);
  }
}

}  // namespace bin_common
