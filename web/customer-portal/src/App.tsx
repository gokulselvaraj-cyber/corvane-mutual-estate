import { Routes, Route, Navigate } from "react-router-dom";
import { QuotePage } from "./pages/QuotePage";
import { PolicyView } from "./pages/PolicyView";
import { FnolWizard } from "./fnol/FnolWizard";
import { RequireRole } from "./auth/RequireRole";
import { Home } from "./pages/Home";

/** Route table. Every route except Home and quotes needs the CUSTOMER role from the Corvane identity provider. */
export function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/quote/:line" element={<QuotePage />} />
      <Route path="/policies/:policyNumber" element={<RequireRole role="CUSTOMER"><PolicyView /></RequireRole>} />
      <Route path="/claims/new" element={<RequireRole role="CUSTOMER"><FnolWizard /></RequireRole>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
