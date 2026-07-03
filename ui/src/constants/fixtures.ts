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

export const FIXTURE_DESCRIPTIONS: Record<string, { label: string; scenario: string }> = {
  support_refund_happy_001: {
    label: "UC1 — Happy path",
    scenario: "Duplicate charge detected, policy allows refund, transaction completes cleanly.",
  },
  support_refund_timeout_after_commit_001: {
    label: "UC2 — Timeout after commit",
    scenario:
      "API times out after refund commits. VERA rechecks business state and stops safely — no duplicate refund.",
  },
  support_refund_high_value_reject_001: {
    label: "UC3 — High-value approval rejected",
    scenario:
      "Refund amount ($750) exceeds threshold. Manager rejects. No refund created, ticket moved to manual review.",
  },
  support_refund_no_duplicate_001: {
    label: "UC4 — No duplicate charge",
    scenario:
      "Customer claims duplicate but only one payment exists. Policy denies refund, ticket routed to follow-up.",
  },
  support_tool_mismatch_001: {
    label: "UC5 — State mismatch escalation",
    scenario:
      "Tool returns success but observed state delta does not match declared transition. VERA escalates and halts.",
  },
};
