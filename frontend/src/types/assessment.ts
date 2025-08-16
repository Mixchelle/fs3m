export type AssessmentBucket = {
  level: "FUNCTION" | "CATEGORY" | "CONTROL";
  code: string;
  name: string;
  order: number;
  metrics: any;
};

export type Assessment = {
  id: number;
  framework: any;
  assessment_type: any;
  summary: { media_geral: number; objetivo: number; status: string };
  buckets: AssessmentBucket[];
};
