export type AuditReceipt = {
  receipt_id: string;
  workflow_id: string;
  action_id: string;
  intended_transition: string;
  observed_transition: string;
  policy_decision: string;
  pre_state_hash: string;
  post_state_hash: string;
  outcome: string;
};

export type TimelineEvent = {
  event_id: string;
  workflow_id: string;
  event_type: string;
  summary: string;
  receipt_id: string | null;
  state_hash: string | null;
};

export type WorkflowResult = {
  workflow_id: string;
  status: string;
  desired_transition_id: string | null;
  policy_decision: string | null;
  final_state_match: boolean;
  audit_receipt_ids: string[];
  audit_receipts: AuditReceipt[];
  timeline_events: TimelineEvent[];
  final_state: Record<string, unknown> | null;
  approval_id?: string | null;
  mismatch_detail?: Record<string, unknown> | null;
  message?: string | null;
};

export type ApprovalRecord = {
  approval_id: string;
  status: string;
  decided_by?: string | null;
  comment?: string | null;
};

export type EvalMetrics = {
  total_tasks: number;
  business_task_success_rate: number;
  final_state_exact_match_rate: number;
  desired_transition_match_rate: number;
  forbidden_transition_count: number;
  duplicate_refund_count: number;
  approval_recall: number;
  rejection_compliance_rate: number;
  audit_completeness_rate: number;
};

export type EvalRepeatedRunSummary = {
  task_count: number;
  total_runs: number;
  task_success_counts: Record<string, number>;
};

export type EvalTaskRow = {
  run_index: number;
  task_id: string;
  fixture_id: string;
  status: string;
  policy_decision: string | null;
  final_state_match: boolean;
  audit_receipts: number;
};

export type ComparisonRow = {
  safeflow: number;
  baseline: number;
  delta?: number;
};

export type EvalResult = {
  run_id: string;
  status: string;
  benchmark_path: string;
  repeated_runs: number;
  pass_k?: number;
  metrics: EvalMetrics;
  repeated_run_summary: EvalRepeatedRunSummary;
  tasks: EvalTaskRow[];
  comparison?: Record<string, ComparisonRow>;
};
