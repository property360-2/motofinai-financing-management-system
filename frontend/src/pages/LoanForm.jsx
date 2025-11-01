import React, { useState } from "react";
import axios from "axios";
import Navbar from "../components/Navbar";

export default function LoanForm() {
  const token = localStorage.getItem("token");
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    employmentStatus: "",
    monthlyIncome: "",
    motorId: "",
    termId: "",
    totalAmount: "",
  });

  const next = () => setStep(step + 1);
  const prev = () => setStep(step - 1);

  const submitLoan = async () => {
    await axios.post("http://localhost:5000/api/loans", form, {
      headers: { Authorization: `Bearer ${token}` },
    });
    alert("Loan submitted!");
    window.location.href = "/finance/loans";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-3xl mx-auto bg-white shadow rounded-xl p-6 mt-6">
        <h2 className="text-xl font-bold mb-4">New Loan Application</h2>
        {step === 1 && (
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="First Name" className="border p-2 rounded" onChange={(e)=>setForm({...form,firstName:e.target.value})}/>
            <input placeholder="Last Name" className="border p-2 rounded" onChange={(e)=>setForm({...form,lastName:e.target.value})}/>
            <input placeholder="Email" className="border p-2 rounded col-span-2" onChange={(e)=>setForm({...form,email:e.target.value})}/>
            <input placeholder="Phone" className="border p-2 rounded col-span-2" onChange={(e)=>setForm({...form,phone:e.target.value})}/>
          </div>
        )}
        {step === 2 && (
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="Employment Status" className="border p-2 rounded" onChange={(e)=>setForm({...form,employmentStatus:e.target.value})}/>
            <input placeholder="Monthly Income" type="number" className="border p-2 rounded" onChange={(e)=>setForm({...form,monthlyIncome:e.target.value})}/>
          </div>
        )}
        {step === 3 && (
          <div className="grid grid-cols-2 gap-4">
            <input placeholder="Motor ID" type="number" className="border p-2 rounded" onChange={(e)=>setForm({...form,motorId:e.target.value})}/>
            <input placeholder="Term ID" type="number" className="border p-2 rounded" onChange={(e)=>setForm({...form,termId:e.target.value})}/>
            <input placeholder="Total Amount" type="number" className="border p-2 rounded col-span-2" onChange={(e)=>setForm({...form,totalAmount:e.target.value})}/>
          </div>
        )}

        <div className="flex justify-between mt-6">
          {step > 1 && (
            <button onClick={prev} className="bg-gray-300 px-4 py-2 rounded">Back</button>
          )}
          {step < 3 ? (
            <button onClick={next} className="bg-blue-600 text-white px-4 py-2 rounded">Next</button>
          ) : (
            <button onClick={submitLoan} className="bg-green-600 text-white px-4 py-2 rounded">Submit</button>
          )}
        </div>
      </div>
    </div>
  );
}
