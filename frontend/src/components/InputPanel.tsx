import { useState } from "react";
import { ImproveConfig } from "../types";

interface InputPanelProps {
  onSubmit: (prompt: string, config: ImproveConfig) => void;
  isRunning: boolean;
}

export function InputPanel({ onSubmit, isRunning }: InputPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [config, setConfig] = useState<ImproveConfig>({
    depth: "quick",
    target_model: "",
    backend: "claude",
  });
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) {
      setValidationError("Prompt cannot be empty.");
      return;
    }
    setValidationError(null);
    onSubmit(prompt, config);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-xl shadow p-6 flex flex-col gap-4"
    >
      <h2 className="text-lg font-semibold text-gray-800">Input Prompt</h2>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="Paste your prompt here..."
        rows={6}
        className="w-full border border-gray-300 rounded-lg p-3 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
      />

      {validationError && (
        <p className="text-red-600 text-sm">{validationError}</p>
      )}

      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Backend
          </label>
          <select
            value={config.backend}
            onChange={(e) =>
              setConfig({ ...config, backend: e.target.value as "claude" | "ollama" | "devin" })
            }
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="claude">Claude (via CLI)</option>
            <option value="ollama">Ollama (local)</option>
            <option value="devin">Devin</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Depth
          </label>
          <select
            value={config.depth}
            onChange={(e) =>
              setConfig({ ...config, depth: e.target.value as "quick" | "thorough" })
            }
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="quick">Quick (2 generations)</option>
            <option value="thorough">Thorough (5 generations)</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Target model (optional)
          </label>
          <input
            type="text"
            value={config.target_model}
            onChange={(e) => setConfig({ ...config, target_model: e.target.value })}
            placeholder="e.g. llama3.2"
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isRunning}
        className="w-full bg-indigo-600 text-white font-semibold py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isRunning ? "Improving..." : "Improve Prompt"}
      </button>
    </form>
  );
}
