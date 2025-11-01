import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { UserContext } from "../context/UserContext";

export default function Navbar() {
  const { user, logout } = useContext(UserContext);

  if (!user) return null;

  const links =
    user.role === "admin"
      ? [
          { to: "/admin", label: "Dashboard" },
          { to: "/admin/motors", label: "Motors" },
          { to: "/admin/financing-terms", label: "Financing Terms" },
        ]
      : [
          { to: "/finance", label: "Dashboard" },
          { to: "/finance/loans", label: "Loans" },
          { to: "/finance/financing-terms", label: "Financing Terms" },
        ];

  return (
    <nav className="bg-blue-700 text-white px-6 py-3 flex justify-between items-center">
      <h1 className="font-bold text-lg">MotofinAI</h1>
      <div className="flex gap-4">
        {links.map((l) => (
          <Link key={l.to} to={l.to} className="hover:text-blue-200">
            {l.label}
          </Link>
        ))}
        <button
          onClick={logout}
          className="bg-red-500 px-3 py-1 rounded-md hover:bg-red-600"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
