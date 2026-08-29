import { useRef, useState } from "react";
import { api } from "../services/api";

export default function FileUpload({ onUploaded, compact }) {
  const inputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleFiles(fileList) {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      const results = await api.uploadFiles(fileList);
      onUploaded?.(results);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    handleFiles(e.dataTransfer.files);
  }

  return (
    <div>
      <div
        className={`upload-zone ${compact ? "upload-zone-compact" : ""}`}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          hidden
          onChange={(e) => handleFiles(e.target.files)}
          accept=".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.html,.css,.sql,.json,.md"
        />
        <p>{uploading ? "Uploading and indexing..." : "Drop code files here or click to upload"}</p>
        <span className="upload-hint">.py .js .jsx .ts .tsx .java .c .cpp .html .css .sql .json .md</span>
      </div>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}
