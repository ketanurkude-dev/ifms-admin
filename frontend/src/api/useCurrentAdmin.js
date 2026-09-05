import { useEffect, useState } from "react";
import { get } from "./apiService";

// Loads the logged-in admin's own profile once, so any page can show
// their name/role and the per-portal permissions without re-fetching.
export function useCurrentAdmin() {
  const [admin, setAdmin] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    get("/auth/me")
      .then(setAdmin)
      .catch(() => setAdmin(null));
  }, []);

  return admin;
}
