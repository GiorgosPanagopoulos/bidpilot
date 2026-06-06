import { create } from "zustand";
import { draftsApi } from "../api/drafts";
import { tendersApi } from "../api/tenders";
import type { BidDraft, Tender, TraceStep } from "../api/types";

interface DraftState {
  selectedTender: Tender | null;
  isIngesting: boolean;
  ingestError: string | null;
  isDrafting: boolean;
  draft: BidDraft | null;
  trace: TraceStep[] | null;
  draftError: string | null;
  selectTender: (tender: Tender) => void;
  ingestDoc: (tenderId: string) => Promise<void>;
  runDraft: (companyId: string, tenderId: string) => Promise<void>;
  fetchTrace: (draftId: string) => Promise<void>;
  clearDraft: () => void;
}

export const useDraftStore = create<DraftState>((set) => ({
  selectedTender: null,
  isIngesting: false,
  ingestError: null,
  isDrafting: false,
  draft: null,
  trace: null,
  draftError: null,

  selectTender: (tender) => set({ selectedTender: tender, draft: null, trace: null }),

  ingestDoc: async (tenderId) => {
    set({ isIngesting: true, ingestError: null });
    try {
      await tendersApi.ingestDoc(tenderId);
    } catch (e) {
      set({ ingestError: e instanceof Error ? e.message : "Ingest failed" });
    } finally {
      set({ isIngesting: false });
    }
  },

  runDraft: async (companyId, tenderId) => {
    set({ isDrafting: true, draftError: null, draft: null, trace: null });
    try {
      // TODO: upgrade to SSE if the backend adds streaming support
      const draft = await draftsApi.run(companyId, tenderId);
      set({ draft });
    } catch (e) {
      set({ draftError: e instanceof Error ? e.message : "Drafting failed" });
    } finally {
      set({ isDrafting: false });
    }
  },

  fetchTrace: async (draftId) => {
    try {
      const trace = await draftsApi.getTrace(draftId);
      set({ trace });
    } catch {
      // trace fetch is non-critical
    }
  },

  clearDraft: () => set({ draft: null, trace: null, draftError: null }),
}));
