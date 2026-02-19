import { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function SourceCard({ source }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3 text-xs">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-gray-400 font-medium">
              {source.source || "unknown"} · Page {source.page ?? "?"}
            </span>
            <span className="text-blue-400 font-mono">
              score: {typeof source.score === "number" ? source.score.toFixed(4) : "—"}
            </span>
          </div>
          <p className="text-gray-300 leading-relaxed">
            {expanded
              ? source.text
              : source.text?.slice(0, 150) + (source.text?.length > 150 ? "…" : "")}
          </p>
        </div>
      </div>
      {source.text?.length > 150 && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-2 text-blue-400 hover:text-blue-300 transition-colors"
        >
          {expanded ? "Collapse ↑" : "Expand ↓"}
        </button>
      )}
    </div>
  );
}

function Message({ msg }) {
  const [showSources, setShowSources] = useState(false);
  const isInsufficient =
    msg.answer?.toLowerCase().includes("don't have enough information");

  return (
    <div className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] space-y-2 ${msg.role === "user" ? "items-end" : "items-start"} flex flex-col`}>
        {/* Bubble */}
        <div
          className={`px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            msg.role === "user"
              ? "bg-blue-600 text-white rounded-br-sm"
              : isInsufficient
              ? "bg-amber-900/40 border border-amber-700 text-amber-200 rounded-bl-sm"
              : "bg-gray-800 text-gray-100 rounded-bl-sm"
          }`}
        >
          {msg.role === "assistant" && isInsufficient && (
            <span className="block text-amber-400 text-xs font-medium mb-1">
              ⚠ Insufficient context
            </span>
          )}
          {msg.answer ?? msg.text}
        </div>

        {/* Sources toggle */}
        {msg.role === "assistant" && msg.sources?.length > 0 && (
          <div className="w-full space-y-2">
            <button
              onClick={() => setShowSources((v) => !v)}
              className="text-xs text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
            >
              <span>{showSources ? "▾" : "▸"}</span>
              <span>
                {showSources ? "Hide" : "Show"} sources ({msg.sources.length})
              </span>
            </button>
            {showSources && (
              <div className="space-y-2">
                {msg.sources.map((src, i) => (
                  <SourceCard key={i} source={src} />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function Chat({ documents }) {
  const [selectedDocId, setSelectedDocId] = useState("");
  const [messages, setMessages] = useState([]); // [{role, text|answer, sources}]
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);

  // Auto-select first doc when documents change
  useEffect(() => {
    if (documents.length > 0 && !selectedDocId) {
      setSelectedDocId(documents[0].doc_id);
    }
  }, [documents]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = async () => {
    const q = input.trim();
    if (!q || loading) return;

    setInput("");
    setError(null);
    setMessages((prev) => [...prev, { role: "user", text: q }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: q,
          doc_id: selectedDocId || null,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Query failed");

      setMessages((prev) => [
        ...prev,
        { role: "assistant", answer: data.answer, sources: data.sources },
      ]);
    } catch (err) {
      setError(err.message);
      setMessages((prev) => prev.slice(0, -1)); // remove the user message on error
      setInput(q); // restore input
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-12rem)]">
      {/* Document selector */}
      {documents.length > 0 && (
        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm text-gray-500 whitespace-nowrap">Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 text-gray-200 text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-blue-500"
          >
            <option value="">All documents</option>
            {documents.map((doc) => (
              <option key={doc.doc_id} value={doc.doc_id}>
                {doc.filename} ({doc.chunks_stored} chunks)
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Empty state */}
      {documents.length === 0 && (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-gray-600 space-y-2">
            <p className="text-3xl">💬</p>
            <p className="text-sm">No documents uploaded yet.</p>
            <p className="text-xs">Go to the Upload tab to add a document first.</p>
          </div>
        </div>
      )}

      {/* Messages */}
      {documents.length > 0 && (
        <>
          <div className="flex-1 overflow-y-auto space-y-4 pr-1 scroll-smooth">
            {messages.length === 0 && (
              <div className="text-center text-gray-600 text-sm py-12">
                Ask a question about your document.
              </div>
            )}
            {messages.map((msg, i) => (
              <Message key={i} msg={msg} />
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full" />
                  <span className="text-gray-400 text-sm">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Error */}
          {error && (
            <div className="mt-2 bg-red-900/30 border border-red-700 rounded-lg px-4 py-2">
              <p className="text-red-400 text-xs">{error}</p>
            </div>
          )}

          {/* Input */}
          <div className="mt-4 flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question… (Enter to send, Shift+Enter for newline)"
              rows={2}
              className="flex-1 bg-gray-900 border border-gray-700 focus:border-blue-500 outline-none text-gray-100 text-sm rounded-xl px-4 py-3 resize-none placeholder:text-gray-600 transition-colors"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded-xl transition-colors text-sm font-medium self-end"
            >
              Send
            </button>
          </div>
        </>
      )}
    </div>
  );
}
