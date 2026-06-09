import { GenerationEvent, Scores } from "../types";
import { ScoreBar } from "./ScoreBar";

const SCORE_KEYS: (keyof Scores)[] = [
  "token_efficiency",
  "format_control",
  "clarity",
  "specificity",
  "hallucination_resistance",
];

interface EvolutionViewerProps {
  events: GenerationEvent[];
  isRunning: boolean;
}

export function EvolutionViewer({ events, isRunning }: EvolutionViewerProps) {
  const generationEvents = events.filter((e) => e.type === "generation");

  if (generationEvents.length === 0 && !isRunning) return null;

  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">
        Evolution Progress
        {isRunning && (
          <span className="ml-2 text-sm text-indigo-500 animate-pulse">
            Running...
          </span>
        )}
      </h2>

      <div className="space-y-4">
        {generationEvents.map((event, idx) => {
          const prev = idx > 0 ? generationEvents[idx - 1].scores : undefined;
          return (
            <div
              key={event.generation}
              className="border border-gray-100 rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-gray-700">
                  {event.generation === 0
                    ? "Original"
                    : `Generation ${event.generation}`}
                </span>
                <span className="text-xs text-gray-400 font-mono">
                  Overall: {event.scores.overall}
                </span>
              </div>

              {SCORE_KEYS.map((key) => (
                <ScoreBar
                  key={key}
                  label={key}
                  value={event.scores[key]}
                  prevValue={prev?.[key]}
                />
              ))}

              {event.reflection && event.generation > 0 && (
                <div className="mt-3 p-3 bg-gray-50 rounded text-xs text-gray-600 italic">
                  <span className="font-semibold not-italic text-gray-700">
                    Reflection:{" "}
                  </span>
                  {event.reflection}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
