import { useEffect, useState } from "react";
import { get, post } from "../api/apiService";
import AppLayout from "./AppLayout";

const PORTAL_LABEL = { employee: "Employee", pension: "Pension", vendor: "Vendor" };
const PORTAL_BADGE = {
  employee: "bg-blue-50 text-blue-700 border-blue-200",
  pension: "bg-purple-50 text-purple-700 border-purple-200",
  vendor: "bg-amber-50 text-amber-700 border-amber-200",
};

export default function Queue() {
  const [items, setItems] = useState(null);
  const [portalFilter, setPortalFilter] = useState("");
  const [activeItem, setActiveItem] = useState(null);
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function loadQueue() {
    setItems(null);
    get("/queue").then(setItems).catch(() => setItems([]));
  }

  useEffect(loadQueue, []);

  async function handleDecision(item, action) {
    if (action === "Returned" && !remarks) {
      setError("Remarks are required to return an item");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await post("/queue/review", {
        source_portal: item.source_portal,
        entity_type: item.entity_type,
        entity_id: item.entity_id,
        action,
        remarks: remarks || null,
      });
      setActiveItem(null);
      setRemarks("");
      loadQueue();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not submit the review");
    } finally {
      setBusy(false);
    }
  }

  const visibleItems = (items || []).filter((item) => !portalFilter || item.source_portal === portalFilter);

  return (
    <AppLayout>
      <div className="bg-white border border-slate-200 rounded p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">Review queue</h1>
            <p className="text-sm text-slate-500">Pending requests pulled live from every portal you can review.</p>
          </div>
          <select
            className="border border-slate-300 rounded-md px-3 py-1.5 text-sm"
            value={portalFilter}
            onChange={(e) => setPortalFilter(e.target.value)}
          >
            <option value="">All portals</option>
            <option value="employee">Employee</option>
            <option value="pension">Pension</option>
            <option value="vendor">Vendor</option>
          </select>
        </div>

        {items === null && <p className="text-sm text-slate-400">Loading queue...</p>}
        {items !== null && visibleItems.length === 0 && (
          <p className="text-sm text-slate-400">Nothing pending review right now.</p>
        )}

        <div className="space-y-3">
          {visibleItems.map((item) => (
            <div key={`${item.source_portal}-${item.entity_type}-${item.entity_id}`} className="border border-slate-200 rounded-md p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-medium border rounded px-2 py-0.5 ${PORTAL_BADGE[item.source_portal]}`}>
                      {PORTAL_LABEL[item.source_portal] || item.source_portal}
                    </span>
                    <span className="text-xs text-slate-400">{item.entity_type}</span>
                  </div>
                  <p className="text-sm font-medium text-slate-800">{item.title}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {item.applicant_name || "Unknown applicant"}
                    {item.application_date ? ` · Applied on ${item.application_date.slice(0, 10)}` : ""}
                  </p>
                </div>
                <button
                  onClick={() => {
                    setActiveItem(activeItem === item ? null : item);
                    setRemarks("");
                    setError("");
                  }}
                  className="shrink-0 text-sm font-medium text-slate-700 border border-slate-300 rounded-md px-3 py-1.5 hover:bg-slate-50"
                >
                  {activeItem === item ? "Close" : "Review"}
                </button>
              </div>

              {activeItem === item && (
                <div className="mt-4 pt-4 border-t border-slate-100">
                  {error && (
                    <div className="mb-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md px-3 py-2">{error}</div>
                  )}

                  {item.details && item.details.length > 0 ? (
                    <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2 mb-4 bg-slate-50 border border-slate-200 rounded-md p-3">
                      {item.details.map((d) => (
                        <div key={d.label}>
                          <dt className="text-xs text-slate-400">{d.label}</dt>
                          <dd className="text-sm text-slate-800 break-words">{String(d.value)}</dd>
                        </div>
                      ))}
                    </dl>
                  ) : (
                    <p className="text-sm text-slate-400 mb-4">No further details were provided for this item.</p>
                  )}

                  <textarea
                    className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm mb-3"
                    rows={2}
                    placeholder="Remarks (required to return an item)"
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <button
                      disabled={busy}
                      onClick={() => handleDecision(item, "Approved")}
                      className="bg-green-700 text-white rounded-md px-4 py-1.5 text-sm font-medium hover:bg-green-800 disabled:opacity-60"
                    >
                      Approve
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => handleDecision(item, "Rejected")}
                      className="bg-red-700 text-white rounded-md px-4 py-1.5 text-sm font-medium hover:bg-red-800 disabled:opacity-60"
                    >
                      Reject
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => handleDecision(item, "Returned")}
                      className="border border-slate-300 text-slate-700 rounded-md px-4 py-1.5 text-sm font-medium hover:bg-slate-50 disabled:opacity-60"
                    >
                      Return for correction
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
