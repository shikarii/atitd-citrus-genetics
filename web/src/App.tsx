import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";

const Landing = lazy(() => import("./pages/Landing").then((m) => ({ default: m.Landing })));
const Methods = lazy(() => import("./pages/Methods").then((m) => ({ default: m.Methods })));
const Models = lazy(() => import("./pages/Models").then((m) => ({ default: m.Models })));
const MIMatrix = lazy(() => import("./pages/MIMatrix").then((m) => ({ default: m.MIMatrix })));
const Anomalies = lazy(() => import("./pages/Anomalies").then((m) => ({ default: m.Anomalies })));
const Residuals = lazy(() => import("./pages/Residuals").then((m) => ({ default: m.Residuals })));
const RSweep = lazy(() => import("./pages/RSweep").then((m) => ({ default: m.RSweep })));
const DistributionTests = lazy(() => import("./pages/DistributionTests").then((m) => ({ default: m.DistributionTests })));
const MixtureModels = lazy(() => import("./pages/MixtureModels").then((m) => ({ default: m.MixtureModels })));
const GeneLandscape = lazy(() => import("./pages/GeneLandscape").then((m) => ({ default: m.GeneLandscape })));
const LitterDetail = lazy(() => import("./pages/LitterDetail").then((m) => ({ default: m.LitterDetail })));

function PageLoading() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="text-slate-400 text-sm">Loading...</div>
    </div>
  );
}

export function App() {
  return (
    <Layout>
      <Suspense fallback={<PageLoading />}>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/methods" element={<Methods />} />
          <Route path="/results/models" element={<Models />} />
          <Route path="/results/mi-matrix" element={<MIMatrix />} />
          <Route path="/results/anomalies" element={<Anomalies />} />
          <Route path="/results/residuals" element={<Residuals />} />
          <Route path="/results/r-sweep" element={<RSweep />} />
          <Route path="/results/distribution" element={<DistributionTests />} />
          <Route path="/results/mixture" element={<MixtureModels />} />
          <Route path="/results/genes" element={<GeneLandscape />} />
          <Route path="/litter/:name" element={<LitterDetail />} />
        </Routes>
      </Suspense>
    </Layout>
  );
}
