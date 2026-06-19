export type ExtractedFields = {
  claimantName: string | null;
  claimType: string | null;
  hospitalizationPeriod: string | null;
  treatmentDate: string | null;
  eventDateOrPeriod: string | null;
  diagnosis: string | null;
  submittedDocuments: string[];
};

export type ClaimAnalysisResponse = {
  claimType: string | null;
  extractedFields: ExtractedFields;
  summary: string;
  reviewChecklist: string[];
  governanceNotice: string;
};

export type RagSource = {
  id: string;
  title: string;
  section: string;
};

export type RagQueryResponse = {
  answer: string;
  sources: RagSource[];
};
