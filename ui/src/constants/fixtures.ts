export const FIXTURE_IDS = [
  "support_refund_happy_001",
  "support_refund_timeout_after_commit_001",
  "support_refund_high_value_reject_001",
  "support_refund_no_duplicate_001",
  "support_tool_mismatch_001",
] as const;

export type FixtureId = (typeof FIXTURE_IDS)[number];

export const DEFAULT_REQUEST_TEXT =
  "I was charged twice for order A102. Refund me now.";
