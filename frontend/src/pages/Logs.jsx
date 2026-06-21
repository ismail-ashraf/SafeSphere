import { useMemo, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Badge from "../components/Badge.jsx";
import { formatDate, maxRiskScore, normalizeDecision, percent, riskFromScore } from "../utils/format.js";

const filters = ["All", "Approved", "Rejected", "Needs Review", "Image", "Text", "Combined"];

export default function Logs({ logs }) {
  const [activeFilter, setActiveFilter] = useState("All");
  const filteredLogs = useMemo(() => {
    if (activeFilter === "All") return logs;
    if (["Image", "Text", "Combined"].includes(activeFilter)) {
      return logs.filter((item) => item.type === activeFilter);
    }
    return logs.filter((item) => normalizeDecision(item.result) === activeFilter);
  }, [logs, activeFilter]);

  return (
    <>
      <PageHeader
        eyebrow="History"
        title="Moderation Logs"
        description="Track previous moderation checks from this browser session."
      />

      <div className="filter-row">
        {filters.map((filter) => (
          <button key={filter} className={activeFilter === filter ? "active" : ""} onClick={() => setActiveFilter(filter)}>
            {filter}
          </button>
        ))}
      </div>

      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Content</th>
              <th>Type</th>
              <th>Decision</th>
              <th>Risk</th>
              <th>Created</th>
              <th>Review</th>
            </tr>
          </thead>
          <tbody>
            {filteredLogs.length === 0 ? (
              <tr><td colSpan="6" className="empty-cell">No logs found for this filter.</td></tr>
            ) : filteredLogs.map((item) => {
              const decision = normalizeDecision(item.result);
              const score = maxRiskScore(item.result);
              const risk = riskFromScore(score);
              return (
                <tr key={item.id}>
                  <td>{item.previewText || item.fileName || "Content item"}</td>
                  <td>{item.type}</td>
                  <td><Badge tone={decision === "Rejected" ? "danger" : decision === "Needs Review" ? "warning" : "success"}>{decision}</Badge></td>
                  <td><Badge tone={risk === "High" ? "danger" : risk === "Medium" ? "warning" : "success"}>{percent(score)}</Badge></td>
                  <td>{formatDate(item.createdAt)}</td>
                  <td>{item.reviewStatus || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
