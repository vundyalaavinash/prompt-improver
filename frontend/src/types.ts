export interface Scores {
  token_efficiency: number;
  format_control: number;
  clarity: number;
  specificity: number;
  hallucination_resistance: number;
  overall: number;
}

export interface Candidate {
  prompt: string;
  scores: Scores;
  reflection: string;
  generation: number;
}

export interface GenerationEvent {
  type: "generation" | "done" | "error";
  generation: number;
  prompt: string;
  scores: Scores;
  reflection: string;
  top_candidates?: Candidate[];
  message?: string;
}

export interface ImproveConfig {
  depth: "quick" | "thorough";
  target_model: string;
  backend: "claude" | "ollama";
}
