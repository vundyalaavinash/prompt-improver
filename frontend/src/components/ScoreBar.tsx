const DIMENSION_LABELS: Record<string, string> = {
  token_efficiency: "Token Efficiency",
  format_control: "Format Control",
  clarity: "Clarity",
  specificity: "Specificity",
  hallucination_resistance: "Hallucination Resistance",
  overall: "Overall",
};

function colorForScore(score: number): string {
  if (score >= 70) return "bg-green-500";
  if (score >= 40) return "bg-yellow-500";
  return "bg-red-500";
}

interface ScoreBarProps {
  label: string;
  value: number;
  prevValue?: number;
}

export function ScoreBar({ label, value, prevValue }: ScoreBarProps) {
  const displayLabel = DIMENSION_LABELS[label] ?? label;
  const delta = prevValue !== undefined ? value - prevValue : null;

  return (
    <div className="mb-2">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{displayLabel}</span>
        <span className="font-mono font-semibold">
          {value}
          {delta !== null && (
            <span className={delta >= 0 ? "text-green-600 ml-1" : "text-red-600 ml-1"}>
              {delta >= 0 ? `+${delta}` : delta}
            </span>
          )}
        </span>
      </div>
      <div className="h-2 bg-gray-200 rounded">
        <div
          className={`h-2 rounded transition-all duration-500 ${colorForScore(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}
