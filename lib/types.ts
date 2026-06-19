export type Letter = "A" | "B" | "C" | "D";

export type Question = {
  qid: string;
  wid: string;
  major: string;
  middle: string;
  minor: string;
  detail: string;
  term: string;
  meaning: string;
  level: string;
  question: string;
  choices: Record<Letter, string>;
  answer: Letter;
};

export type QuizRecord = { correct_count: number; wrong_count: number; last_date: string };
export type RecordsMap = Map<string, QuizRecord>; // qid -> record
export type ChecksMap = Map<string, Partial<Record<1 | 2 | 3, string>>>; // wid -> {slot: date}

export const LETTERS: Letter[] = ["A", "B", "C", "D"];
export const ORDINALS: Record<1 | 2 | 3, string> = { 1: "1st", 2: "2nd", 3: "3rd" };
