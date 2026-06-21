import Badge from "./Badge.jsx";
import { percent } from "../utils/format.js";

function toneFromRisk(risk) {
  if (risk === "High" || risk === "Rejected") return "danger";
  if (risk === "Medium" || risk === "Needs Review") return "warning";
  if (risk === "Low" || risk === "Approved") return "success";
  return "neutral";
}

export default function ResultCard({ title, result, type }) {
  if (!result) {
    return (
      <div className="card result-card empty">
        <h3>{title}</h3>
        <p>No analysis yet.</p>
      </div>
    );
  }

  const risk = result.risk_level || result.final_decision || "Low";

  return (
    <div className="card result-card">
      <div className="card-title-row">
        <h3>{title}</h3>
        <Badge tone={toneFromRisk(risk)}>{risk}</Badge>
      </div>

      {type === "image" && (
        <div className="score-list">
          <div><span>Prediction</span><strong>{result.prediction || "—"}</strong></div>
          <div><span>Violence Score</span><strong>{percent(result.violence_score)}</strong></div>
          <div><span>Safe Score</span><strong>{percent(result.safe_score)}</strong></div>
          <div><span>Confidence</span><strong>{result.confidence || percent(result.confidence_percentage)}</strong></div>
        </div>
      )}

      {type === "text" && (
        <div className="score-list">
          <div><span>Status</span><strong>{result.is_toxic ? "Toxic" : "Clean"}</strong></div>
          <div><span>Toxic Score</span><strong>{percent(result.toxic_score ?? result.toxic_confidence_percentage)}</strong></div>
          <div><span>Clean Score</span><strong>{percent(result.clean_score)}</strong></div>
          <div><span>Processing</span><strong>{result.processing_time_ms || "—"} ms</strong></div>
        </div>
      )}

      {type === "decision" && (
        <div className="decision-block">
          <strong>{result.final_decision}</strong>
          <p>{result.reason}</p>
          <span>{result.recommended_action}</span>
        </div>
      )}
    </div>
  );
}
