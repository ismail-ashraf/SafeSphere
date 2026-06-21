import { useEffect, useState } from "react";
import { Loader2, Play } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import UploadBox from "../components/UploadBox.jsx";
import ResultCard from "../components/ResultCard.jsx";
import { analyzeImage } from "../api/client.js";
import { addLog } from "../utils/storage.js";

export default function ImageModeration({ onLogsChange }) {
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
    if (!file) {
      setError("Upload an image first.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const payload = await analyzeImage(file);
      setResult(payload);
      const next = addLog({ type: "Image", result: payload, fileName: file.name });
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
        eyebrow="Vision Model"
        title="Image Violence Detection"
        description="Upload an image and let the TensorFlow model classify violent vs non-violent content."
      />

      <div className="content-grid two-cols">
        <div className="card input-card">
          <h3>Upload Image</h3>
          <UploadBox file={file} preview={preview} onChange={setFile} onClear={() => setFile(null)} />
          {error && <div className="alert error">{error}</div>}
          <button className="primary-button full" onClick={handleAnalyze} disabled={loading}>
            {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
            {loading ? "Analyzing..." : "Analyze Image"}
          </button>
        </div>
        <ResultCard title="Image Result" type="image" result={result} />
      </div>
    </>
  );
}
