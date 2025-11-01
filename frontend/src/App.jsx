import React, { useContext } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { UserContext } from "./context/UserContext";
import Login from "./pages/Login";
import AdminDashboard from "./pages/AdminDashboard";
import FinanceDashboard from "./pages/FinanceDashboard";
import ProtectedRoute from "./routes/ProtectedRoute";
import RoleRedirect from "./routes/RoleRedirect";
import MotorInventory from "./pages/MotorInventory";
import LoanList from "./pages/LoanList";
import LoanForm from "./pages/LoanForm";
import FinancingTerms from "./pages/FinancingTerms";
const App = () => {
  const { user } = useContext(UserContext);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RoleRedirect user={user} />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/admin/motors" element={<MotorInventory />} />
        <Route path="/admin/financing-terms" element={<FinancingTerms />} />
        <Route path="/finance" element={<FinanceDashboard />} />
        <Route path="/finance/loans" element={<LoanList />} />
        <Route path="/finance/loans/new" element={<LoanForm />} />
        <Route path="/finance/financing-terms" element={<FinancingTerms />} />
      </Route>

      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
};

export default App;
