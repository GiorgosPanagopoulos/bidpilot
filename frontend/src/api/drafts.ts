import { api } from "./client";
import type { BidDraft, TraceStep } from "./types";

export const draftsApi = {
  run: (companyId: string, tenderId: string) =>
    api.post<BidDraft>("/drafts/run", { company_id: companyId, tender_id: tenderId }),
  get: (draftId: string) => api.get<BidDraft>(`/drafts/${draftId}`),
  getTrace: (draftId: string) => api.get<TraceStep[]>(`/drafts/${draftId}/trace`),
};
