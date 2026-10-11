#include "citrus/dispatch.h"
#include "citrus/avx2.h"

#ifdef CITRUS_CUDA_ENABLED
#include "citrus/kernels.h"
#endif

namespace citrus {
namespace dispatch {

bool has_avx2() {
    return avx2::is_available();
}

bool has_cuda() {
#ifdef CITRUS_CUDA_ENABLED
    return cuda::is_available();
#else
    return false;
#endif
}

std::string cuda_device_name() {
#ifdef CITRUS_CUDA_ENABLED
    if (cuda::is_available()) {
        return cuda::device_name();
    }
#endif
    return "";
}

} // namespace dispatch
} // namespace citrus
