import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import Layout from "@/components/Layout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Income from "@/pages/Income";
import Expenses from "@/pages/Expenses";
import FuelPage from "@/pages/Fuel";
import Trucks from "@/pages/Trucks";
import Loads from "@/pages/Loads";
import Drivers from "@/pages/Drivers";
import Inspections from "@/pages/Inspections";
import TestData from "@/pages/TestData";

function Protected() {
  const { user } = useAuth();
  if (user === null) return <div className="flex min-h-screen items-center justify-center bg-[#0B0F17] font-mono text-sm text-slate-500">Loading…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <Layout />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<Protected />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/income" element={<Income />} />
            <Route path="/expenses" element={<Expenses />} />
            <Route path="/fuel" element={<FuelPage />} />
            <Route path="/trucks" element={<Trucks />} />
            <Route path="/loads" element={<Loads />} />
            <Route path="/drivers" element={<Drivers />} />
            <Route path="/inspections" element={<Inspections />} />
            <Route path="/test-data" element={<TestData />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <Toaster theme="dark" position="bottom-right" />
    </AuthProvider>
  );
}

export default App;
