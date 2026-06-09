import { useState, useCallback } from "react";
import { Candidate, GenerationEvent, ImproveConfig } from "../types";

export function useImprove() {
  const [events, setEvents] = useState<GenerationEvent[]>([]);
  const [topCandidates, setTopCandidates] = useState<Candidate[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const improve = useCallback(async (prompt: string, config: ImproveConfig) => {
    setEvents([]);
    setTopCandidates([]);
    setError(null);
    setIsRunning(true);

    try {
      const response = await fetch("/api/improve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, ...config }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        for (const line of text.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          const event: GenerationEvent = JSON.parse(line.slice(6));
          setEvents((prev) => [...prev, event]);
          if (event.type === "done" && event.top_candidates) {
            setTopCandidates(event.top_candidates);
          }
          if (event.type === "error") {
            setError(event.message ?? "Unknown error");
          }
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsRunning(false);
    }
  }, []);

  return { events, topCandidates, isRunning, error, improve };
}
