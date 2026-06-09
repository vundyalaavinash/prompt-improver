import * as Diff from "diff";
import { Candidate, Scores } from "../types";
import { ScoreBar } from "./ScoreBar";

const SCORE_KEYS: (keyof Scores)[] = [
  "token_efficiency",
  "format_control",
  "clarity",
  "specificity",
  "hallucination_resistance",
];

function DiffView({ original, improved }: { original: string; improved: string }) {
  const parts = Diff.diffWords(original, improved);
  return (
    <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-50 rounded p-3 leading-relaxed">
      {parts.map((part, i) => (
        <span
          key={i}
          className={
            part.added
              ? "bg-green-100 text-green-800"
              : part.removed
              ? "bg-red-100 text-red-800 line-through"
              : "text-gray-700"
          }
        >
          {part.value}
        </span>
      ))}
    </pre>
  );
}

interface ResultsPanelProps {
  topCandidates: Candidate[];
  originalPrompt: string;
  originalScores?: Scores;
}

export function ResultsPanel({
  topCandidates,
  originalPrompt,
  originalScores,
}: ResultsPanelProps) {
  if (topCandidates.length === 0) return null;

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
  }

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Top Results ({topCandidates.length})
      </h2>

      <div className="space-y-6">
        {topCandidates.map((candidate, idx) => (
          <div key={idx} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-indigo-700">
                #{idx + 1} — Generation {candidate.generation} — Overall:{" "}
                {candidate.scores.overall}
              </span>
              <button
                onClick={() => copyToClipboard(candidate.prompt)}
                className="text-xs text-indigo-600 hover:text-indigo-800 border border-indigo-200 rounded px-2 py-1 transition-colors"
              >
                Copy
              </button>
            </div>

            <div className="mb-3">
              {SCORE_KEYS.map((key) => (
                <ScoreBar
                  key={key}
                  label={key}
                  value={candidate.scores[key]}
                  prevValue={originalScores?.[key]}
                />
              ))}
            </div>

            <div className="mb-3">
              <p className="text-xs font-medium text-gray-500 mb-1">
                What changed:
              </p>
              <DiffView original={originalPrompt} improved={candidate.prompt} />
            </div>

            <div className="p-3 bg-indigo-50 rounded text-sm text-gray-800 font-mono">
              {candidate.prompt}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
