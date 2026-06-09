import { useImprove } from "./hooks/useImprove";
import { InputPanel } from "./components/InputPanel";
import { EvolutionViewer } from "./components/EvolutionViewer";
import { ResultsPanel } from "./components/ResultsPanel";
import { ImproveConfig, Scores } from "./types";
import { useState } from "react";

export default function App() {
  const { events, topCandidates, isRunning, error, improve } = useImprove();
  const [originalPrompt, setOriginalPrompt] = useState("");

  function handleSubmit(prompt: string, config: ImproveConfig) {
    setOriginalPrompt(prompt);
    improve(prompt, config);
  }

  const gen0Scores = events.find((e) => e.generation === 0)?.scores as Scores | undefined;

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Prompt Improver</h1>
          <p className="text-gray-500 mt-1 text-sm">
            GEPA-powered evolutionary prompt optimization
          </p>
        </div>

        <InputPanel onSubmit={handleSubmit} isRunning={isRunning} />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm">
            Error: {error}
          </div>
        )}

        <EvolutionViewer events={events} isRunning={isRunning} />

        <ResultsPanel
          topCandidates={topCandidates}
          originalPrompt={originalPrompt}
          originalScores={gen0Scores}
        />
      </div>
    </div>
  );
}
