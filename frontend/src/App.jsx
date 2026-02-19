import { useState } from "react";
import Upload from "./Upload";
import Chat from "./Chat";

export default function App() {
  const [activeTab, setActiveTab] = useState("upload");
  const [documents, setDocuments] = useState([]); // [{ doc_id, filename, chunks_stored }]

  const handleUploadSuccess = (doc) => {
    setDocuments((prev) => [...prev, doc]);
    setActiveTab("chat");
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-mono">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center gap-4">
        <div>
          <h1 className="text-xl font-bold text-white tracking-tight">
            RAG From Scratch
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">
            No LangChain. Pure Python. By Amit Saraswat
          </p>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-800 px-6">
        <div className="flex gap-0">
          {["upload", "chat"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 text-sm font-medium capitalize transition-colors border-b-2 ${
                activeTab === tab
                  ? "border-blue-500 text-blue-400"
                  : "border-transparent text-gray-500 hover:text-gray-300"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <main className="max-w-4xl mx-auto px-4 py-8">
        {activeTab === "upload" && (
          <Upload onUploadSuccess={handleUploadSuccess} />
        )}
        {activeTab === "chat" && (
          <Chat documents={documents} />
        )}
      </main>
    </div>
  );
}
