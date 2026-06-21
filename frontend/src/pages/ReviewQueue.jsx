import PageHeader from "../components/PageHeader.jsx";
import Badge from "../components/Badge.jsx";
import { formatDate, maxRiskScore, normalizeDecision, percent, riskFromScore } from "../utils/format.js";
import { updateLog } from "../utils/storage.js";

export default function ReviewQueue({ logs, onLogsChange }) {
  const reviewItems = logs.filter((item) => normalizeDecision(item.result) === "Needs Review" || item.reviewStatus === "pending");

  function handleAction(id, status) {
    onLogsChange(updateLog(id, { reviewStatus: status }));
  }

  return (
    <>
      <PageHeader
        eyebrow="Human Review"
        title="Review Queue"
        description="Review uncertain model decisions and mark them as approved, rejected, or false positive."
      />

      <div className="card table-card">
        <table>
          <thead>
            <tr>
              <th>Content</th>
              <th>Type</th>
              <th>Risk</th>
              <th>AI Decision</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {reviewItems.length === 0 ? (
              <tr><td colSpan="6" className="empty-cell">No items need review right now.</td></tr>
            ) : reviewItems.map((item) => {
              const score = maxRiskScore(item.result);
              const risk = riskFromScore(score);
              return (
                <tr key={item.id}>
                  <td>{item.previewText || item.fileName || "Content item"}</td>
                  <td>{item.type}</td>
                  <td><Badge tone={risk === "High" ? "danger" : risk === "Medium" ? "warning" : "success"}>{percent(score)}</Badge></td>
                  <td>{normalizeDecision(item.result)}</td>
                  <td>{formatDate(item.createdAt)}</td>
                  <td className="actions-cell">
                    <button onClick={() => handleAction(item.id, "approved")}>Approve</button>
                    <button onClick={() => handleAction(item.id, "rejected")}>Reject</button>
                    <button onClick={() => handleAction(item.id, "false_positive")}>False Positive</button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
