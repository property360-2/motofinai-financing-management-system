import React, { useEffect, useState } from "react";
import axios from "axios";

export default function Dashboard() {
  const [data, setData] = useState([]);
  const token = localStorage.getItem("token");

  useEffect(() => {
    if (!token) return;

    axios
      .get("http://localhost:5000/api/users", {
        headers: { Authorization: `Bearer ${token}` },
      })
      .then((res) => setData(res.data))
      .catch(() => {});
  }, [token]);

  return (
    <div style={{ padding: "2rem" }}>
      <h1>Dashboard</h1>
      <table border="1" cellPadding="5">
        <thead>
          <tr><th>ID</th><th>Username</th><th>Email</th><th>Role</th><th>Status</th></tr>
        </thead>
        <tbody>
          {data.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td><td>{u.username}</td><td>{u.email}</td><td>{u.role}</td><td>{u.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
