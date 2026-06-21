export function percent(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return "—";
  const numeric = Number(value);
  return `${(numeric <= 1 ? numeric * 100 : numeric).toFixed(1)}%`;
}

export function normalizeDecision(result) {
  if (!result) return "Unknown";
  if (result.final_decision) return result.final_decision;
  if (result.is_toxic || result.is_violence || result.prediction === "Violence") return "Rejected";
  return "Approved";
}

export function maxRiskScore(result) {
  if (!result) return 0;
  const scores = [
    result?.image_result?.violence_score,
    result?.text_result?.toxic_score,
    result?.violence_score,
    result?.toxic_score,
  ].filter((score) => score !== undefined && score !== null);
  return scores.length ? Math.max(...scores.map(Number)) : 0;
}

export function riskFromScore(score) {
  if (score >= 0.75) return "High";
  if (score >= 0.5) return "Medium";
  return "Low";
}

export function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
