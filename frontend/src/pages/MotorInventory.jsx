import React, { useEffect, useState, useContext, useCallback } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";
import { UserContext } from "../context/UserContext";

export default function MotorInventory() {
  const { user } = useContext(UserContext);
  const [motors, setMotors] = useState([]);
  const [form, setForm] = useState({
    type: "",
    brand: "",
    model: "",
    year: "",
    purchasePrice: "",
    status: "available",
  });
  const isAdmin = user?.role === "admin";

  const token = localStorage.getItem("token");

  const fetchMotors = useCallback(async () => {
    if (!token) return;

    try {
      const res = await axios.get("http://localhost:5000/api/motors", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMotors(res.data);
    } catch (error) {
      console.error("Failed to load motors", error);
    }
  }, [token]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!isAdmin) return;

    try {
      await axios.post("http://localhost:5000/api/motors", form, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setForm({
        type: "",
        brand: "",
        model: "",
        year: "",
        purchasePrice: "",
        status: "available",
      });
      fetchMotors();
    } catch (error) {
      console.error("Failed to add motor", error);
      window.alert(error.response?.data?.message ?? "Unable to add motor");
    }
  };

  const handleDelete = async (id) => {
    if (!confirm("Archive this motor?")) return;
    try {
      await axios.delete(`http://localhost:5000/api/motors/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      fetchMotors();
    } catch (error) {
      console.error("Failed to archive motor", error);
      window.alert(error.response?.data?.message ?? "Unable to archive motor");
    }
  };

  useEffect(() => {
    fetchMotors();
  }, [fetchMotors]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="p-6">
        <h1 className="text-3xl font-bold text-blue-700 mb-4">Motor Inventory</h1>

        {/* Add Form */}
        {isAdmin && (
          <form
            onSubmit={handleAdd}
            className="grid lg:grid-cols-6 md:grid-cols-3 gap-3 bg-white p-4 rounded-xl shadow mb-5"
          >
            <input
              required
              placeholder="Type"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
              value={form.type}
              onChange={(e) => setForm({ ...form, type: e.target.value })}
            />
            <input
              required
              placeholder="Brand"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
              value={form.brand}
              onChange={(e) => setForm({ ...form, brand: e.target.value })}
            />
            <input
              required
              placeholder="Model"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
              value={form.model}
              onChange={(e) => setForm({ ...form, model: e.target.value })}
            />
            <input
              required
              type="number"
              placeholder="Year"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
              value={form.year}
              onChange={(e) => setForm({ ...form, year: e.target.value })}
            />
            <input
              required
              type="number"
              step="0.01"
              placeholder="Purchase Price"
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
              value={form.purchasePrice}
              onChange={(e) => setForm({ ...form, purchasePrice: e.target.value })}
            />
            <select
              value={form.status}
              onChange={(e) => setForm({ ...form, status: e.target.value })}
              className="border p-2 rounded-lg focus:ring focus:ring-blue-300"
            >
              {["available", "reserved", "sold", "repossessed"].map((status) => (
                <option key={status} value={status}>
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </option>
              ))}
            </select>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Add</button>
          </form>
        )}

        {/* Table */}
        <table className="w-full text-left bg-white shadow rounded-lg overflow-hidden">
          <thead className="bg-blue-100">
            <tr>
              <th className="p-3">ID</th>
              <th className="p-3">Type</th>
              <th className="p-3">Brand</th>
              <th className="p-3">Model</th>
              <th className="p-3">Status</th>
              <th className="p-3">Price</th>
              {isAdmin && <th className="p-3">Action</th>}
            </tr>
          </thead>
          <tbody>
            {motors.map((m) => (
              <tr key={m.id} className="border-t hover:bg-gray-50">
                <td className="p-3">{m.id}</td>
                <td className="p-3">{m.type}</td>
                <td className="p-3">{m.brand}</td>
                <td className="p-3">{m.model}</td>
                <td className="p-3 capitalize">{m.status}</td>
                <td className="p-3">PHP {m.purchasePrice}</td>
                {isAdmin && (
                  <td className="p-3">
                    <button
                      onClick={() => handleDelete(m.id)}
                      className="text-red-600 hover:text-red-800 font-semibold"
                    >
                      Archive
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
