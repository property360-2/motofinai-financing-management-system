import React  from "react";
import { UserContext } from "../context/UserContext";
import Navbar from "../components/Navbar";

export default function AdminDashboard() {

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <Navbar />
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-blue-700">Admin Dashboard</h1>
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl shadow">Total Loans</div>
        <div className="bg-white p-4 rounded-xl shadow">Pending Applications</div>
        <div className="bg-white p-4 rounded-xl shadow">Overdue Payments</div>
      </div>
    </div>
  );
}
