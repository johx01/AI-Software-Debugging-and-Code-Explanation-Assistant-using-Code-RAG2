import { useRef, useState } from "react";
import { api } from "../services/api";

const ACCEPT = ".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.html,.css,.sql,.json,.md";

export default function FileUpload({ onUploaded, compact }) {
  const inputRef = useRef(null);
  const folderInputRef = useRef(null);
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
      if (folderInputRef.current) folderInputRef.current.value = "";
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    const items = e.dataTransfer.items;
    if (items && items.length && items[0].webkitGetAsEntry) {
      collectDroppedEntries(items).then(handleFiles);
    } else {
      handleFiles(e.dataTransfer.files);
    }
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
          accept={ACCEPT}
        />
        <input
          ref={folderInputRef}
          type="file"
          hidden
          webkitdirectory=""
          directory=""
          multiple
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p>{uploading ? "Uploading and indexing..." : "Drop code files or a folder here, or click to upload"}</p>
        <span className="upload-hint">.py .js .jsx .ts .tsx .java .c .cpp .html .css .sql .json .md</span>
        <button
          type="button"
          className="upload-folder-btn"
          disabled={uploading}
          onClick={(e) => {
            e.stopPropagation();
            folderInputRef.current?.click();
          }}
        >
          Upload folder
        </button>
      </div>
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

// Drag-and-drop of a folder gives DataTransferItems whose entries must be
// walked recursively to collect every File inside (the DOM's File input
// with `webkitdirectory` does this automatically, but drop events don't).
async function collectDroppedEntries(items) {
  const entries = Array.from(items)
    .map((item) => item.webkitGetAsEntry?.())
    .filter(Boolean);

  const files = [];
  async function walk(entry, path) {
    if (entry.isFile) {
      await new Promise((resolve) => {
        entry.file((file) => {
          const relativePath = path + entry.name;
          try {
            Object.defineProperty(file, "webkitRelativePath", { value: relativePath });
          } catch {
            // ignore if the property can't be redefined
          }
          files.push(file);
          resolve();
        });
      });
    } else if (entry.isDirectory) {
      const reader = entry.createReader();
      const children = await new Promise((resolve) => reader.readEntries(resolve));
      for (const child of children) {
        await walk(child, `${path}${entry.name}/`);
      }
    }
  }

  for (const entry of entries) {
    await walk(entry, "");
  }
  return files;
}
