#pragma once

// CUDA kernel declarations
// These are stubs when CUDA is not available

#ifdef CITRUS_CUDA_ENABLED

namespace citrus {
namespace cuda {

bool is_available();
const char* device_name();

} // namespace cuda
} // namespace citrus

#endif // CITRUS_CUDA_ENABLED
