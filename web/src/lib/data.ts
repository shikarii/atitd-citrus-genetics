/** Typed data loaders for pre-computed analysis JSON in public/data/. */

const BASE = import.meta.env.BASE_URL + "data/";

async function fetchJson<T>(filename: string): Promise<T> {
  const res = await fetch(BASE + filename);
  if (!res.ok) throw new Error(`Failed to load ${filename}: ${res.status}`);
  return res.json() as Promise<T>;
}

async function fetchText(filename: string): Promise<string> {
  const res = await fetch(BASE + filename);
  if (!res.ok) throw new Error(`Failed to load ${filename}: ${res.status}`);
  return res.text();
}

// --- Type definitions ---

export interface ModelComparison {
  model: string;
  fit_ll: number;
  cv_ll: number;
  children_impossible: number;
  [key: string]: string | number; // per-litter ll_ columns
}

export interface MIEntry {
  parent_var: string;
  child_var: string;
  mi_observed: number;
  mi_shuffled_mean: number;
  mi_excess: number;
  mi_excess_z: number;
  is_diagonal: boolean;
}

export interface AnomalyScore {
  litter: string;
  child_idx: number;
  child_num: number;
  log_lik: number;
  rank: number;
  A_color: number; A_sweet: number; A_size: number; A_length: number;
  B_color: number; B_sweet: number; B_size: number; B_length: number;
  color: number; sweet: number; size: number; length: number;
}

export interface ResidualEntry {
  litter: string;
  child_idx: number;
  child_num: number;
  color_residual: number;
  sweet_residual: number;
  size_residual: number;
  length_residual: number;
}

export interface SiblingCorrelation {
  litter: string;
  trait: string;
  n_children: number;
  pearson_r: number;
  p_value: number;
}

export interface RSweepEntry {
  R: number;
  fit_ll: number;
  cv_ll: number;
  delta_fit: number;
  delta_cv: number;
}

export interface DistributionTest {
  litter: string;
  trait: string;
  n_observed: number;
  ks_stat: number;
  ks_pvalue: number;
  ks_pvalue_fdr: number;
  ks_sig_fdr: boolean;
  ad_stat: number;
  ad_sig_5pct: boolean;
}

export interface MixtureWeight {
  litter: string;
  n: number;
  pi_claim: number;
  pi_indep: number;
  log_lik_mixture: number;
  log_lik_claim_only: number;
  delta_ll: number;
}

export interface FittedGenes {
  litter: string;
  loglik: number;
  clone_share: number;
  [key: string]: string | number; // A_color_genes, B_sweet_genes, etc.
}

export interface Child {
  litter: string;
  child: number;
  A_color: number; A_sweet: number; A_size: number; A_length: number;
  B_color: number; B_sweet: number; B_size: number; B_length: number;
  color: number; sweet: number; size: number; length: number;
}

export interface RunMeta {
  run_id: string;
  timestamp: string;
  source_data_hash: string;
  n_children: number;
  n_litters: number;
}

export type TraitCooccurrence = Record<string, Record<string, number>>;

// --- Loaders ---

export const loadModelComparison = () => fetchJson<ModelComparison[]>("model_comparison.json");
export const loadMIMatrix = () => fetchJson<MIEntry[]>("mi_matrix.json");
export const loadAnomalyScores = () => fetchJson<AnomalyScore[]>("anomaly_scores.json");
export const loadResiduals = () => fetchJson<ResidualEntry[]>("residuals.json");
export const loadSiblingCorrelations = () => fetchJson<SiblingCorrelation[]>("sibling_correlations.json");
export const loadTraitCooccurrence = () => fetchJson<TraitCooccurrence>("trait_cooccurrence.json");
export const loadRSweep = () => fetchJson<RSweepEntry[]>("r_sweep.json");
export const loadDistributionTests = () => fetchJson<DistributionTest[]>("distribution_tests.json");
export const loadMixtureWeights = () => fetchJson<MixtureWeight[]>("mixture_weights.json");
export const loadFittedGenes = () => fetchJson<FittedGenes[]>("fitted_genes.json");
export const loadChildren = () => fetchJson<Child[]>("children.json");
export const loadRunMeta = () => fetchJson<RunMeta>("run_meta.json");
export const loadMethodology = () => fetchText("methodology.md");

export interface AnalysisInterpretation {
  key: string;
  title: string;
  findings: string[];
  stats: Record<string, string | number>;
}

export type Interpretations = Record<string, AnalysisInterpretation>;

export const loadInterpretations = () => fetchJson<Interpretations>("interpretations.json");

export const TRAITS = ["color", "sweet", "size", "length"] as const;
export type Trait = (typeof TRAITS)[number];
export const LITTERS = [
  "Hive1", "Hive2", "Hive3", "Hive4", "Hive5", "Hive6", "Hive7",
  "Hive8", "Hive9", "Hive10", "Hive11", "Hive1a", "Hive1b", "Hive1c",
] as const;
