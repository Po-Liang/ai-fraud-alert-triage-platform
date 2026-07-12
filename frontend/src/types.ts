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
  excerpt?: string;
  sourceType?: "demo_internal_guideline";
};

export type RagMetadata = {
  knowledgeBase: "insurance_claims" | "fraud_alerts";
  retrievalStatus: "COMPLETED" | "NO_EVIDENCE" | "FAILED";
  groundingStatus: "GROUNDED" | "NOT_GROUNDED";
  generationMode:
    | "OPENAI"
    | "DETERMINISTIC_FALLBACK"
    | "MOCK_DETERMINISTIC"
    | "NOT_RUN";
  model?: string;
};

export type RagQueryResponse = {
  answer: string;
  sources: RagSource[];
  metadata?: RagMetadata;
};

export type AlertInput = {
  customerId: string;
  accountId: string;
  alertType: string;
  amount: number;
  currency: string;
  country: string;
  description: string;
  historicalAverageAmount: number;
  isNewBeneficiary: boolean;
  transactionCountLastHour: number;
};

export type AlertAnalysisResult = {
  riskScore: number;
  riskLevel: "LOW" | "MEDIUM" | "HIGH";
  signals: string[];
  aiSummary: string;
  recommendedActions: string[];
};

export type ReviewAction = "APPROVE" | "REQUEST_REANALYSIS" | "ESCALATE" | "CLOSE";

export type ReviewEvent = {
  reviewEventId: string;
  action: ReviewAction;
  reviewedAt: string;
  workflowRunId: string;
  workflowVersion: string;
  comment?: string;
};

export type FraudAlert = AlertInput & {
  alertId: string;
  status: "PENDING_ANALYSIS" | "ANALYSIS_IN_PROGRESS" | "ANALYSIS_COMPLETED";
  createdAt: string;
  updatedAt: string;
  analysisResult?: AlertAnalysisResult;
  reviewStatus?: ReviewAction;
  reviewHistory?: ReviewEvent[];
};

export type ReviewResponse = {
  alertId: string;
  reviewStatus: ReviewAction;
  reviewEvent: ReviewEvent;
};

export type WorkflowStageStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "waiting_for_human";

export type WorkflowStage = {
  stageId: "triage" | "evidence" | "planning" | "human_review";
  stageName: string;
  logicalAgentRole: string;
  status: WorkflowStageStatus;
  inputSummary: string;
  outputSummary: string;
  startedAt?: string;
  completedAt?: string;
  durationMs?: number;
  error?: string;
};

export type InvestigationTaskStatus =
  | "planned"
  | "running"
  | "completed"
  | "failed"
  | "waiting_for_human";

export type InvestigationTask = {
  taskId: string;
  taskType:
    | "confirm_customer_profile"
    | "review_recent_transactions"
    | "inspect_related_accounts"
    | "retrieve_guidelines"
    | "identify_missing_information"
    | "escalation_review";
  description: string;
  status: InvestigationTaskStatus;
  assignedAgent: string;
  evidence: string[];
  requiresHumanApproval: boolean;
};
