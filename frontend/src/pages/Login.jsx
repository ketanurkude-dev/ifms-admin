import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { post } from "../api/apiService";
import AuthLayout from "./AuthLayout";

export default function Login() {
  const navigate = useNavigate();
  const [staffCode, setStaffCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await post("/auth/login", { staff_code: staffCode, password });
      // Login is step 1 of 2. Carry the pending_token to the OTP page.
      sessionStorage.setItem("pending_token", data.pending_token);
      navigate("/otp");
    } catch (err) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout title="Staff sign in" subtitle="Enter your staff code and password to continue">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="mb-5 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="staff_code">
            Staff code
          </label>
          <input
            id="staff_code"
            placeholder="ADMIN001"
            className="w-full border border-slate-300 rounded-md px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-700 focus:border-slate-700"
            value={staffCode}
            onChange={(e) => setStaffCode(e.target.value)}
            required
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-700 mb-1.5" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            className="w-full border border-slate-300 rounded-md px-3.5 py-2.5 text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-700 focus:border-slate-700"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-slate-900 text-white rounded-md py-2.5 font-medium hover:bg-slate-800 transition-colors disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-xs text-slate-400 mt-6 text-center">
          Demo accounts: ADMIN001 / admin123 (all portals), STAFF001 / staff123 (employee only)
        </p>
      </form>
    </AuthLayout>
  );
}
