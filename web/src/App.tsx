import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Landing } from "./pages/Landing";
import { Methods } from "./pages/Methods";
import { Models } from "./pages/Models";
import { MIMatrix } from "./pages/MIMatrix";
import { Anomalies } from "./pages/Anomalies";
import { Residuals } from "./pages/Residuals";
import { RSweep } from "./pages/RSweep";
import { DistributionTests } from "./pages/DistributionTests";
import { MixtureModels } from "./pages/MixtureModels";
import { GeneLandscape } from "./pages/GeneLandscape";
import { LitterDetail } from "./pages/LitterDetail";

export function App() {
  return (
    <Layout>
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
    </Layout>
  );
}
