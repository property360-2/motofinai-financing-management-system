import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";

export default function LoanList() {
  const [loans, setLoans] = useState([]);
  const token = localStorage.getItem("token");

  const fetchLoans = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get("http://localhost:5000/api/loans", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLoans(res.data);
    } catch (error) {
      console.error("Failed to fetch loans", error);
    }
  }, [token]);

  useEffect(() => {
    fetchLoans();
  }, [fetchLoans]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4 text-green-700">Loan Applications</h1>
        <table className="w-full bg-white shadow rounded-lg overflow-hidden">
          <thead className="bg-green-100">
            <tr>
              <th className="p-3">#</th>
              <th className="p-3">Applicant</th>
              <th className="p-3">Motor</th>
              <th className="p-3">Status</th>
              <th className="p-3">Term</th>
              <th className="p-3">Amount</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan) => (
              <tr key={loan.id} className="border-t hover:bg-gray-50">
                <td className="p-3">{loan.id}</td>
                <td className="p-3">
                  {loan.firstName} {loan.lastName}
                </td>
                <td className="p-3">
                  {loan.motor?.brand} {loan.motor?.model}
                </td>
                <td className="p-3 capitalize">{loan.applicationStatus}</td>
                <td className="p-3">{loan.term?.termYears} yr</td>
                <td className="p-3">PHP {loan.totalAmount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
