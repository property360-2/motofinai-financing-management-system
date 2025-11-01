import React, { useCallback, useContext, useEffect, useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";
import { UserContext } from "../context/UserContext";

export default function FinancingTerms() {
  const { user } = useContext(UserContext);
  const isAdmin = user?.role === "admin";
  const token = localStorage.getItem("token");

  const [terms, setTerms] = useState([]);
  const [form, setForm] = useState({ termYears: "", interestRate: "" });
  const [loading, setLoading] = useState(false);

  const fetchTerms = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get("http://localhost:5000/api/financing-terms", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTerms(res.data);
    } catch (error) {
      console.error("Failed to load financing terms", error);
    }
  }, [token]);

  useEffect(() => {
    fetchTerms();
  }, [fetchTerms]);

  const handleChange = (key) => (event) => {
    setForm((prev) => ({ ...prev, [key]: event.target.value }));
  };

  const handleCreate = async (event) => {
    event.preventDefault();
    if (!isAdmin) return;

    setLoading(true);
    try {
      await axios.post("http://localhost:5000/api/financing-terms", form, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setForm({ termYears: "", interestRate: "" });
      fetchTerms();
    } catch (error) {
      console.error("Failed to create term", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRate = async (term) => {
    if (!isAdmin) return;
    const nextRate = window.prompt(
      `Set new interest rate for ${term.termYears}-year term`,
      term.interestRate
    );
    if (!nextRate && nextRate !== 0) return;

    try {
      await axios.patch(
        `http://localhost:5000/api/financing-terms/${term.id}`,
        { interestRate: nextRate },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchTerms();
    } catch (error) {
      console.error("Failed to update term", error);
    }
  };

  const handleDelete = async (term) => {
    if (!isAdmin) return;
    if (!window.confirm(`Delete the ${term.termYears}-year financing term?`)) return;

    try {
      await axios.delete(`http://localhost:5000/api/financing-terms/${term.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchTerms();
    } catch (error) {
      console.error("Failed to delete term", error);
      window.alert(error.response?.data?.message ?? "Unable to delete financing term");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-blue-700">Financing Terms</h1>
        </div>

        {isAdmin && (
          <form
            onSubmit={handleCreate}
            className="bg-white shadow rounded-xl p-5 mb-6 grid md:grid-cols-3 gap-4"
          >
            <input
              required
              min="1"
              max="7"
              type="number"
              value={form.termYears}
              onChange={handleChange("termYears")}
              placeholder="Term (years)"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
            />
            <input
              required
              type="number"
              step="0.1"
              value={form.interestRate}
              onChange={handleChange("interestRate")}
              placeholder="Interest Rate (%)"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
            />
            <button
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-300"
            >
              Add Term
            </button>
          </form>
        )}

        <div className="bg-white shadow rounded-xl overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-blue-100">
              <tr>
                <th className="p-3">Years</th>
                <th className="p-3">Interest Rate (%)</th>
                {isAdmin && <th className="p-3 w-48">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {terms.map((term) => (
                <tr key={term.id} className="border-t hover:bg-gray-50">
                  <td className="p-3 font-medium">{term.termYears}</td>
                  <td className="p-3">{Number(term.interestRate).toFixed(2)}</td>
                  {isAdmin && (
                    <td className="p-3 space-x-3">
                      <button
                        type="button"
                        onClick={() => handleUpdateRate(term)}
                        className="text-blue-600 hover:text-blue-800 font-semibold"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(term)}
                        className="text-red-600 hover:text-red-800 font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
