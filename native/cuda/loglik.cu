// CUDA loglik reduction kernel — placeholder for Tier 2 implementation
// When implemented, this will compute log-likelihood sums using
// warp-level reductions for maximum throughput.

#ifdef CITRUS_CUDA_ENABLED

#include <cuda_runtime.h>

namespace citrus {
namespace cuda {

static bool g_cuda_checked = false;
static bool g_cuda_available = false;
static char g_device_name[256] = "";

bool is_available() {
    if (!g_cuda_checked) {
        int count = 0;
        cudaError_t err = cudaGetDeviceCount(&count);
        g_cuda_available = (err == cudaSuccess && count > 0);
        if (g_cuda_available) {
            cudaDeviceProp prop;
            cudaGetDeviceProperties(&prop, 0);
            strncpy(g_device_name, prop.name, sizeof(g_device_name) - 1);
        }
        g_cuda_checked = true;
    }
    return g_cuda_available;
}

const char* device_name() {
    is_available(); // ensure checked
    return g_device_name;
}

} // namespace cuda
} // namespace citrus

#endif // CITRUS_CUDA_ENABLED
