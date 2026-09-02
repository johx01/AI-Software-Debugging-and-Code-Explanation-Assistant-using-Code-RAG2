import { useEffect, useRef, useState } from "react";

const ACCEPT = ".py,.js,.jsx,.ts,.tsx,.java,.c,.cpp,.html,.css,.sql,.json,.md";

export default function ChatInput({ onSend, onFilesSelected, disabled, enterToSend, uploading }) {
  const [value, setValue] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpen]);

  function handleSubmit(e) {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey && enterToSend) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  function handleFileChange(e) {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFilesSelected?.(files);
    }
    e.target.value = "";
  }

  return (
    <form className="chat-input-bar" onSubmit={handleSubmit}>
      <input ref={fileInputRef} type="file" multiple hidden accept={ACCEPT} onChange={handleFileChange} />
      <input
        ref={folderInputRef}
        type="file"
        hidden
        webkitdirectory=""
        directory=""
        multiple
        onChange={handleFileChange}
      />
      <div className="chat-attach" ref={menuRef}>
        <button
          type="button"
          className="btn-attach"
          title="Upload files or a folder"
          disabled={disabled || uploading}
          onClick={() => setMenuOpen((v) => !v)}
        >
          {uploading ? "…" : "+"}
        </button>
        {menuOpen && (
          <div className="chat-attach-menu">
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                fileInputRef.current?.click();
              }}
            >
              Upload files
            </button>
            <button
              type="button"
              onClick={() => {
                setMenuOpen(false);
                folderInputRef.current?.click();
              }}
            >
              Upload folder
            </button>
          </div>
        )}
      </div>
      <textarea
        className="chat-input"
        placeholder="Ask anything about your code..."
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        disabled={disabled}
      />
      <button className="btn-primary" type="submit" disabled={disabled || !value.trim()}>
        Send
      </button>
    </form>
  );
}
