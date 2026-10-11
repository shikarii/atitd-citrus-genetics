"""Analysis pipelines for ATITD citrus genetics research methodology.

Implements the Tier 0-2 analyses from docs/research_methodology.md:
- anomaly: per-child log-likelihood anomaly scoring
- r_sweep: nudge-range parameter sweep
- mi_matrix: mutual information between parent and child traits
- residuals: residual analysis and sibling correlations
- distribution_tests: KS/AD goodness-of-fit tests with FDR correction
- mixture: CLAIM + INDEP mixture model (EM fitting)
- profile: profile likelihoods for hidden genes
"""
