import React from "react";
import { Navigate } from "react-router-dom";

export default function RoleRedirect({ user }) {
  if (!user) return <Navigate to="/login" />;

  switch (user.role) {
    case "admin":
      return <Navigate to="/admin" />;
    case "finance":
      return <Navigate to="/finance" />;
    default:
      return <Navigate to="/login" />;
  }
}
