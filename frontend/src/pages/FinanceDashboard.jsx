import React, { useContext } from "react";
import { UserContext } from "../context/UserContext";

export default function FinanceDashboard() {
  const { logout } = useContext(UserContext);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-green-700">Finance Dashboard</h1>
        <button
          onClick={logout}
          className="bg-red-500 text-white px-4 py-2 rounded-lg hover:bg-red-600"
        >
          Logout
        </button>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl shadow">Payments Overview</div>
        <div className="bg-white p-4 rounded-xl shadow">Risk Distribution</div>
        <div className="bg-white p-4 rounded-xl shadow">Repossession Alerts</div>
      </div>
    </div>
  );
}
