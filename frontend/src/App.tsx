import { FraudInvestigationDemo } from "./components/FraudInvestigationDemo";
import { InsuranceClaimsDemo } from "./components/InsuranceClaimsDemo";

const demoMode = import.meta.env.VITE_DEMO_MODE?.trim() || "nttdata";

export function App() {
  if (demoMode === "insurance") {
    return <main><InsuranceClaimsDemo /></main>;
  }

  return <main><FraudInvestigationDemo /></main>;
}
