import { useEffect, useRef } from "react";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

const EXAMPLE_PROMPTS = [
  "Explain this function",
  "Find potential bugs",
  "How does authentication work?",
  "Where is the database connection?",
  "Explain the project structure",
];

export default function ChatWindow({
  messages,
  onSend,
  onFilesSelected,
  uploading,
  loading,
  showSources,
  enterToSend,
  userName,
}) {
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-window">
      {isEmpty ? (
        <div className="welcome-screen">
          <h2>Welcome{userName ? `, ${userName}` : ""}</h2>
          <p className="welcome-subtitle">AI Code Debugging &amp; Explanation Assistant</p>
          <p className="welcome-description">
            Upload your codebase and ask questions about your code using Retrieval-Augmented Generation.
          </p>
          <div className="example-prompts">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button key={prompt} className="example-prompt" onClick={() => onSend(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div className="message-list">
          {messages.map((m, i) => (
            <ChatMessage
              key={i}
              role={m.role}
              content={m.content}
              sources={m.sources}
              showSources={showSources}
            />
          ))}
          {loading && (
            <div className="chat-message chat-message-bot">
              <div className="chat-message-label">Assistant</div>
              <div className="chat-message-bubble chat-thinking">Thinking...</div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      )}

      <ChatInput
        onSend={onSend}
        onFilesSelected={onFilesSelected}
        uploading={uploading}
        disabled={loading}
        enterToSend={enterToSend}
      />
    </div>
  );
}
