import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneLight, oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import SourceList from "./SourceList";
import { useTheme } from "../services/ThemeContext";

function CodeBlock({ className, children }) {
  const [copied, setCopied] = useState(false);
  const { theme } = useTheme();
  const language = (className || "").replace("language-", "") || "text";
  const code = String(children).replace(/\n$/, "");

  function handleCopy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const isDark =
    theme === "dark" ||
    (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);

  return (
    <div className="code-block">
      <div className="code-block-header">
        <span className="mono">{language}</span>
        <button className="btn-copy" onClick={handleCopy}>
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={isDark ? oneDark : oneLight}
        customStyle={{ margin: 0, borderRadius: "0 0 8px 8px", fontSize: "0.85rem" }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default function ChatMessage({ role, content, sources, showSources }) {
  const isUser = role === "user";

  return (
    <div className={`chat-message ${isUser ? "chat-message-user" : "chat-message-bot"}`}>
      <div className="chat-message-label">{isUser ? "You" : "JohnBot"}</div>
      <div className="chat-message-bubble">
        <ReactMarkdown
          components={{
            code({ inline, className, children }) {
              if (inline) return <code className="mono">{children}</code>;
              return <CodeBlock className={className}>{children}</CodeBlock>;
            },
          }}
        >
          {content}
        </ReactMarkdown>
        {showSources && <SourceList sources={sources} />}
      </div>
    </div>
  );
}
