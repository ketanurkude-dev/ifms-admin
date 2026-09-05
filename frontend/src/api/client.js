import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:9004",
});

// Attach the saved JWT (if any) to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// A 401 means the saved token is missing/expired/invalid -- clear it and
// send the user back to login instead of letting pages silently render
// as if there were just no data.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== "/login") {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
