import { UploadCloud, X } from "lucide-react";

export default function UploadBox({ file, preview, onChange, onClear }) {
  return (
    <div className="upload-box">
      {!file ? (
        <label>
          <UploadCloud size={32} />
          <strong>Upload image</strong>
          <span>Drag or choose JPG, PNG, WEBP</span>
          <input
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            onChange={(event) => onChange(event.target.files?.[0] || null)}
          />
        </label>
      ) : (
        <div className="preview-wrap">
          <button className="icon-button" onClick={onClear} type="button" aria-label="Remove image">
            <X size={16} />
          </button>
          {preview && <img src={preview} alt="Uploaded preview" />}
          <span>{file.name}</span>
        </div>
      )}
    </div>
  );
}
