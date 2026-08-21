import { Navigate, Route, Routes } from "react-router-dom";
import { Shell } from "./components/ui";
import { CompetitorPage } from "./pages/CompetitorPage";
import { DashboardPage } from "./pages/DashboardPage";

export default function App() {
  return <Shell><Routes><Route path="/" element={<DashboardPage />} /><Route path="/competitors/:id" element={<CompetitorPage />} /><Route path="*" element={<Navigate to="/" replace />} /></Routes></Shell>;
}
