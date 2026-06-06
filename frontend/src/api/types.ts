// Mirrors backend Pydantic models. No `any` types.

export interface CompanyProfile {
  id: string;
  name: string;
  cpv_codes: string[];
  regions: string[];
  annual_turnover: number;
  capacity_tags: string[];
  exclusion_flags: string[];
}

export interface Tender {
  id: string;
  source: "TED" | "KIMDIS" | "ESIDIS";
  title: string;
  cpv_codes: string[];
  budget: number | null;
  deadline: string;
  nuts: string[];
  description: string;
  raw_doc_uri: string;
  exclusion_flags: string[];
  status: "open" | "closed" | "awarded";
}

export interface EligibilityCheck {
  passed: boolean;
  failed_criteria: string[];
  warnings: string[];
  rule_version: string;
}

export interface MatchResult {
  tender_id: string;
  company_id: string;
  score: number;
  semantic_score: number;
  rule_score: number;
  reasons: string[];
  eligibility: EligibilityCheck;
}

export interface ProposalCitation {
  tender_id: string;
  locator: string;
  snippet: string;
}

export interface RequirementItem {
  id: string;
  category: "technical" | "financial" | "legal" | "administrative" | "submission";
  text: string;
  mandatory: boolean;
  citation: ProposalCitation;
}

export interface RequirementChecklist {
  tender_id: string;
  items: RequirementItem[];
  extracted_at: string;
  prompt_version: string;
}

export interface GapItem {
  requirement_id: string;
  status: "met" | "partial" | "unmet";
  evidence: string | null;
  note: string | null;
}

export interface GapReport {
  company_id: string;
  tender_id: string;
  items: GapItem[];
  coverage_ratio: number;
}

export interface BidDraftSection {
  title: string;
  content: string;
  citations: ProposalCitation[];
  covers_requirements: string[];
  self_check_status: "ok" | "gaps";
}

export interface BidDraft {
  id: string;
  company_id: string;
  tender_id: string;
  sections: BidDraftSection[];
  checklist: RequirementChecklist;
  gap_report: GapReport;
  status: "needs_review";
  prompt_version: string;
  created_at: string;
  notice: string;
}

export interface TraceStep {
  thought: string;
  action: string;
  action_input: string;
  observation: string;
}

export interface PricingStats {
  cpv: string | null;
  count: number;
  min: number | null;
  max: number | null;
  mean: number | null;
  median: number | null;
  p25: number | null;
  p75: number | null;
  currency: string;
}

export interface SupplierWinRate {
  supplier_name: string;
  supplier_vat: string | null;
  awards_won: number;
  total_value: number;
  win_share: number;
}

export interface TrendPoint {
  period: string;
  count: number;
  total_value: number;
  mean_value: number;
}

export interface TrendSeries {
  interval: "month" | "quarter" | "year";
  points: TrendPoint[];
}

export interface ApiErrorBody {
  detail: string;
}
