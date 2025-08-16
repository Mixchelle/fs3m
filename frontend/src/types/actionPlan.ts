import { Recommendation } from "./recommendation";

export type ActionPlan = {
  id: number;
  cliente: any;
  criado_por: any;
  observacoes: string;
  data_criacao: string;
  data_atualizacao: string;
  prazo?: string;
  gravidade?: string;
  urgencia?: string;
  categoria?: string;
  orcamentoMax?: string;
  submission_id?: number|null;
  recomendacoes: (Recommendation & { ordem: number; status: string; data_alteracao: string })[];
};
