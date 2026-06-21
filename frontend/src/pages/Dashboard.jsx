import PageHeader from "../components/PageHeader.jsx";
import MetricCard from "../components/MetricCard.jsx";
import Badge from "../components/Badge.jsx";
import { formatDate, maxRiskScore, normalizeDecision, percent, riskFromScore } from "../utils/format.js";

export default function Dashboard({ logs }) {
  const total = logs.length;
  const approved = logs.filter((item) => normalizeDecision(item.result) === "Approved").length;
  const rejected = logs.filter((item) => normalizeDecision(item.result) === "Rejected").length;
  const review = logs.filter((item) => normalizeDecision(item.result) === "Needs Review").length;
  const avgRisk = total ? logs.reduce((sum, item) => sum + maxRiskScore(item.result), 0) / total : 0;
  const recent = logs.slice(0, 6);

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title="AI Moderation Dashboard"
        description="Monitor image violence detection and toxic text moderation from one clean control panel."
      />

      <div className="metric-grid">
        <MetricCard label="Total Checks" value={total} helper="Stored locally in this UI" />
        <MetricCard label="Approved" value={approved} helper="Safe content" tone="success" />
        <MetricCard label="Rejected" value={rejected} helper="Blocked content" tone="danger" />
        <MetricCard label="Needs Review" value={review} helper="Manual queue" tone="warning" />
      </div>

      <div className="content-grid two-cols">
        <div className="card chart-card">
          <div className="card-title-row">
            <h3>Decision Distribution</h3>
            <Badge tone="neutral">Live UI Logs</Badge>
          </div>
          <div className="bars">
            <div><span>Approved</span><div><i style={{ width: `${total ? (approved / total) * 100 : 0}%` }} /></div><strong>{approved}</strong></div>
            <div><span>Rejected</span><div><i style={{ width: `${total ? (rejected / total) * 100 : 0}%` }} /></div><strong>{rejected}</strong></div>
            <div><span>Review</span><div><i style={{ width: `${total ? (review / total) * 100 : 0}%` }} /></div><strong>{review}</strong></div>
          </div>
        </div>

        <div className="card chart-card">
          <div className="card-title-row">
            <h3>Average Risk</h3>
            <Badge tone={avgRisk >= 0.75 ? "danger" : avgRisk >= 0.5 ? "warning" : "success"}>{riskFromScore(avgRisk)}</Badge>
          </div>
          <div className="risk-meter">
            <strong>{percent(avgRisk)}</strong>
            <div><i style={{ width: `${Math.min(avgRisk * 100, 100)}%` }} /></div>
            <span>Based on the highest score per moderation request.</span>
          </div>
        </div>
      </div>

      <div className="card table-card">
        <div className="card-title-row">
          <h3>Recent Moderation Activity</h3>
          <Badge>{recent.length} items</Badge>
        </div>
        <table>
          <thead>
            <tr><th>Type</th><th>Decision</th><th>Risk</th><th>Created</th></tr>
          </thead>
          <tbody>
            {recent.length === 0 ? (
              <tr><td colSpan="4" className="empty-cell">Run your first scan from Combined Check.</td></tr>
            ) : recent.map((item) => {
              const decision = normalizeDecision(item.result);
              const score = maxRiskScore(item.result);
              return (
                <tr key={item.id}>
                  <td>{item.type}</td>
                  <td><Badge tone={decision === "Rejected" ? "danger" : decision === "Needs Review" ? "warning" : "success"}>{decision}</Badge></td>
                  <td>{percent(score)}</td>
                  <td>{formatDate(item.createdAt)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
