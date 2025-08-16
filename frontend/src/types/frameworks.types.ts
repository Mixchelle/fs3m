// src/services/frameworks.types.ts

/** === Framework (catálogo) === */
export type Framework = {
  id: number;
  slug: string;
  name: string;
  version: string;
  description: string;
  active: boolean;
  editable: boolean;
  created_at: string;
  updated_at: string;
};

/** === Tipos de suporte (pontuação/opções) === */
export type ChoiceOption = {
  id: number;
  label: string;
  value: string;
  weight: string | null;     // Decimal vindo como string no DRF
  order: number;
  active: boolean;
};

export type ScoringModel = {
  id: number;
  name: string;
  slug: string;
  mapping: Record<string, number>;
  rules: Record<string, any>;
};

/** === Estruturas de Question/Control/Domain === */
export type QuestionItem = {
  id: number;
  control: number;           // PK do controle
  local_code: string;        // ex.: "score", "politica"...
  prompt: string;
  type: string;              // "scale" | "text" | etc (mantém aberto)
  required: boolean;
  order: number;
  meta: Record<string, any>;
  scoring_model: ScoringModel | null;
  options: ChoiceOption[];
};

export type ControlItem = {
  id: number;
  framework: number;
  domain: number;            // PK do domain
  code: string;              // ex.: "GV.OC-01"
  title: string;
  description: string;
  order: number;
  active: boolean;
  scoring_model: ScoringModel | null;
  questions: QuestionItem[];
};

export type DomainItem = {
  id: number;
  framework: number;
  code: string;              // ex.: "GV"
  title: string;             // ex.: "Governança (GV)"
  parent: number | null;
  order: number;
  children: DomainItem[];
  controls: ControlItem[];
};

/** === Template (FormTemplate) === */
export type TemplateDetail = {
  id: number;
  name: string;
  slug: string;
  version: string;
  description: string;
  active: boolean;
  editable: boolean;
  created_at: string;
  updated_at: string;
  framework: {
    id: number;
    slug: string;
    name: string;
    version: string;
    description: string;
    active: boolean;
    editable: boolean;
    created_at: string;
    updated_at: string;
  };
  items: Array<{
    id: number;
    template: number;
    order: number;
    control: ControlItem;          // expandido no serializer
    question: QuestionItem | null; // pode ser null (inclui todas do controle)
  }>;
};
