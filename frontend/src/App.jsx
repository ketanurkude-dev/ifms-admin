import { Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Otp from "./pages/Otp";
import Queue from "./pages/Queue";
import AuditLog from "./pages/AuditLog";

function RequireAuth({ children }) {
  const token = localStorage.getItem("access_token");
  return token ? children : <Navigate to="/login" replace />;
}

const protectedRoutes = [
  { path: "/queue", element: <Queue /> },
  { path: "/audit-log", element: <AuditLog /> },
];

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<Login />} />
      <Route path="/otp" element={<Otp />} />
      {protectedRoutes.map(({ path, element }) => (
        <Route key={path} path={path} element={<RequireAuth>{element}</RequireAuth>} />
      ))}
    </Routes>
  );
}
