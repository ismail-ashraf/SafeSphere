import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import { API_BASE_URL } from "../api/client.js";
import { getSettings, saveSettings } from "../utils/storage.js";

const defaultSettings = {
  imageThreshold: 70,
  textThreshold: 70,
  reviewThreshold: 50,
  maxImageSize: 5,
  allowedTypes: "JPG, PNG, WEBP",
};

export default function Settings() {
  const [settings, setSettings] = useState(defaultSettings);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setSettings({ ...defaultSettings, ...getSettings() });
  }, []);

  function updateField(field, value) {
    setSettings((current) => ({ ...current, [field]: value }));
    setSaved(false);
  }

  function handleSave() {
    saveSettings(settings);
    setSaved(true);
  }

  return (
    <>
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="UI-side settings for thresholds and upload rules. Backend thresholds are controlled from backend/.env."
      />

      <div className="content-grid two-cols">
        <div className="card settings-card">
          <h3>Moderation Thresholds</h3>
          <label>
            <span>Image Violence Threshold</span>
            <input type="number" value={settings.imageThreshold} onChange={(e) => updateField("imageThreshold", Number(e.target.value))} />
          </label>
          <label>
            <span>Text Toxic Threshold</span>
            <input type="number" value={settings.textThreshold} onChange={(e) => updateField("textThreshold", Number(e.target.value))} />
          </label>
          <label>
            <span>Manual Review Starts At</span>
            <input type="number" value={settings.reviewThreshold} onChange={(e) => updateField("reviewThreshold", Number(e.target.value))} />
          </label>
          <button className="primary-button full" onClick={handleSave}>Save UI Settings</button>
          {saved && <div className="alert success">Settings saved in this browser.</div>}
        </div>

        <div className="card settings-card">
          <h3>Integration</h3>
          <label>
            <span>Current API Base URL</span>
            <input value={API_BASE_URL} readOnly />
          </label>
          <label>
            <span>Max Image Size</span>
            <input type="number" value={settings.maxImageSize} onChange={(e) => updateField("maxImageSize", Number(e.target.value))} />
          </label>
          <label>
            <span>Allowed Image Types</span>
            <input value={settings.allowedTypes} onChange={(e) => updateField("allowedTypes", e.target.value)} />
          </label>
          <p className="hint">To change the backend URL, edit frontend/.env and set VITE_API_BASE_URL.</p>
        </div>
      </div>
    </>
  );
}
