#pragma once

#include <string>

namespace citrus {
namespace dispatch {

// Runtime feature detection
bool has_avx2();
bool has_cuda();
std::string cuda_device_name();

} // namespace dispatch
} // namespace citrus
