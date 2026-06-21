import { useEffect, useState } from "react";
import { Loader2, Play } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import UploadBox from "../components/UploadBox.jsx";
import ResultCard from "../components/ResultCard.jsx";
import { analyzeCombined } from "../api/client.js";
import { addLog } from "../utils/storage.js";

export default function CombinedCheck({ onLogsChange }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreview("");
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setPreview(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [file]);

  async function handleAnalyze() {
    if (!text.trim() && !file) {
      setError("Add text, image, or both before running analysis.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const payload = await analyzeCombined({ text: text.trim(), file });
      setResult(payload);
      const next = addLog({ type: "Combined", result: payload, previewText: text.trim().slice(0, 120), fileName: file?.name });
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
        eyebrow="Multi-modal Check"
        title="Combined Content Check"
        description="Analyze uploaded images and written text together using the SafeSphere models."
      />

      <div className="content-grid two-cols">
        <div className="card input-card">
          <h3>Image Input</h3>
          <UploadBox file={file} preview={preview} onChange={setFile} onClear={() => setFile(null)} />
        </div>

        <div className="card input-card">
          <h3>Text Input</h3>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Write or paste user-generated text here..."
          />
          <small>{text.length}/5000 characters</small>
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="center-action">
        <button className="primary-button" onClick={handleAnalyze} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
          {loading ? "Analyzing..." : "Analyze Content"}
        </button>
      </div>

      <div className="content-grid three-cols">
        <ResultCard title="Image Result" type="image" result={result?.image_result} />
        <ResultCard title="Text Result" type="text" result={result?.text_result} />
        <ResultCard title="Final Decision" type="decision" result={result} />
      </div>
    </>
  );
}
