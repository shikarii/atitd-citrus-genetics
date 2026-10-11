// CUDA scan_parent kernel — placeholder for Tier 2 implementation
// When implemented, each CUDA block will evaluate one candidate gene pair,
// with threads cooperatively computing trait_rows and reducing loglik.

#ifdef CITRUS_CUDA_ENABLED

#include <cuda_runtime.h>

namespace citrus {
namespace cuda {
// Future: parallel gene-pair scanning kernel
} // namespace cuda
} // namespace citrus

#endif // CITRUS_CUDA_ENABLED
