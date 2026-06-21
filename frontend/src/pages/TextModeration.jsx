import { useState } from "react";
import { Loader2, Play } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import ResultCard from "../components/ResultCard.jsx";
import { analyzeText } from "../api/client.js";
import { addLog } from "../utils/storage.js";

export default function TextModeration({ onLogsChange }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function handleAnalyze() {
    if (!text.trim()) {
      setError("Write text before running analysis.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const payload = await analyzeText(text.trim());
      setResult(payload);
      const next = addLog({ type: "Text", result: payload, previewText: text.trim().slice(0, 120) });
      onLogsChange(next);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="NLP Model"
        title="Toxic Text Detection"
        description="Analyze text toxicity and show explainability highlights when SHAP is enabled."
      />

      <div className="content-grid two-cols">
        <div className="card input-card">
          <h3>Text to Analyze</h3>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Type a message, comment, or caption..."
          />
          <small>{text.length}/5000 characters</small>
          {error && <div className="alert error">{error}</div>}
          <button className="primary-button full" onClick={handleAnalyze} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            {loading ? "Analyzing..." : "Analyze Text"}
          </button>
        </div>

        <div className="stack">
          <ResultCard title="Text Result" type="text" result={result} />
          {result?.highlighted_html_text && (
            <div className="card highlighted-card">
              <h3>Highlighted Explanation</h3>
              <div dangerouslySetInnerHTML={{ __html: result.highlighted_html_text }} />
            </div>
          )}
        </div>
      </div>
    </>
  );
}
