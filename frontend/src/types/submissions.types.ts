export type SubmissionStatus =
  | "draft"
  | "in_review"
  | "pending"
  | "submitted"
  | "archived";

export type SubmissionItem = {
  id: number;
  status: SubmissionStatus;
  progress: number | string;
  version: number;
  created_at: string;
  updated_at: string;
  template: { id: number; name: string; slug: string; version: string };
  framework: { id: number; name: string; slug: string; version: string };
};

export type SubmissionRead = {
  id: number;
  customer: number;
  template: number;      // ID
  framework: number;     // ID
  status: SubmissionStatus;
  version: number;
  progress: string;
  created_at: string;
  updated_at: string;
};

export export type AnswerItem = {
  id: number;
  submission: number;
  question: number;
  value: Record<string, any> | null; // { policy, practice } etc.
  evidence?: string | null;
  attachment?: string | null;
  created_at?: string;
  updated_at?: string;
};

export export type UpsertAnswerPayload = {
  submission: number;
  question: number;
  value: Record<string, any>; // { policy, practice }
  evidence?: string;
};