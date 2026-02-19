import { useState, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function Upload({ onUploadSuccess }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null); // { doc_id, filename, chunks_stored }
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    const valid = file.name.endsWith(".pdf") || file.name.endsWith(".txt");
    if (!valid) {
      setError("Only PDF and TXT files are supported.");
      return;
    }
    setError(null);
    setResult(null);
    setSelectedFile(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Upload failed");
      }
      setResult(data);
      onUploadSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white">Upload Document</h2>
        <p className="text-sm text-gray-500 mt-1">
          Upload a PDF or TXT file to index it into the vector database.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          dragOver
            ? "border-blue-500 bg-blue-500/5"
            : "border-gray-700 hover:border-gray-500 bg-gray-900/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <div className="text-4xl mb-3">📄</div>
        <p className="text-gray-300 text-sm font-medium">
          Drag & drop or click to select
        </p>
        <p className="text-gray-600 text-xs mt-1">PDF or TXT files only</p>
      </div>

      {/* Selected file info */}
      {selectedFile && !result && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-white font-medium">{selectedFile.name}</p>
            <p className="text-xs text-gray-500 mt-0.5">{formatBytes(selectedFile.size)}</p>
          </div>
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
          >
            {uploading ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
                Uploading...
              </>
            ) : (
              "Upload"
            )}
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {/* Success */}
      {result && (
        <div className="bg-green-900/20 border border-green-700 rounded-xl p-5 space-y-3">
          <div className="flex items-center gap-2 text-green-400 font-medium">
            <span>✓</span>
            <span>Document indexed successfully</span>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-900/60 rounded-lg p-3">
              <p className="text-gray-500 text-xs mb-1">Filename</p>
              <p className="text-white truncate">{result.filename}</p>
            </div>
            <div className="bg-gray-900/60 rounded-lg p-3">
              <p className="text-gray-500 text-xs mb-1">Chunks stored</p>
              <p className="text-white">{result.chunks_stored}</p>
            </div>
          </div>
          <p className="text-gray-400 text-sm">
            Ready to chat — switch to the <strong className="text-blue-400">Chat</strong> tab.
          </p>
        </div>
      )}
    </div>
  );
}
