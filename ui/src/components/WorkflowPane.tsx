import {
  Activity,
  CheckCircle2,
  FileText,
  GitCompare,
  ListChecks,
  Play,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useMemo } from "react";
import { FIXTURE_DESCRIPTIONS, FIXTURE_IDS } from "../constants/fixtures";
import { ApprovalRecord, WorkflowResult } from "../types";
import { formatStatus, shortHash, statusIcon } from "../utils/format";

type Props = {
  requestText: string;
  fixtureId: string;
  result: WorkflowResult | null;
  approval: ApprovalRecord | null;
  isRunning: boolean;
  error: string | null;
  includeBaseline: boolean;
  onRequestTextChange: (v: string) => void;
  onFixtureChange: (v: string) => void;
  onRun: () => void;
  onApprovalDecide: (decision: "approve" | "reject") => void;
  onToggleBaseline: (v: boolean) => void;
};

// Plain-English narrative for each outcome status
const STATUS_NARRATIVE: Record<string, string> = {
  completed:
    "VERA detected a duplicate charge, verified policy, created one refund with an idempotency key, and confirmed the state transition matched the declared effect.",
  completed_with_recovered_timeout:
    "The refund API timed out after committing. VERA rechecked actual business state, detected the committed refund, and stopped safely — zero duplicate refunds.",
  approval_pending:
    "Refund amount exceeds the high-value threshold. VERA gated the action and is waiting for a manager decision before executing.",
  pending_manual_review:
    "Manager rejected the approval. No refund was created. Ticket routed to manual review queue.",
  denied:
    "No duplicate payment found for this order. Policy denied the refund. Ticket routed to customer follow-up.",
  escalated_state_mismatch:
    "Tool returned success, but observed state delta did not match the declared transition effect. VERA escalated and halted all further consequential actions.",
  failed_safe: "VERA could not verify the action outcome and stopped safely to avoid a side effect.",
};

function StateHighlight({ finalState }: { finalState: Record<string, unknown> | null }) {
  if (!finalState) return <p className="muted">No state</p>;

  const refunds = finalState.refunds as Record<string, Record<string, unknown>> | undefined;
  const payments = finalState.payments as Record<string, Record<string, unknown>> | undefined;
  const tickets = finalState.tickets as Record<string, Record<string, unknown>> | undefined;

  const completedRefunds = refunds
    ? Object.values(refunds).filter((r) => r.status === "completed")
    : [];
  const pendingRefunds = refunds
    ? Object.values(refunds).filter((r) => r.status !== "completed")
    : [];
  const capturedPayments = payments
    ? Object.values(payments).filter((p) => p.status === "captured")
    : [];

  const ticketEntry = tickets ? Object.values(tickets)[0] : undefined;

  return (
    <div className="state-highlight">
      <div className="state-kpi-row">
        <div className={`state-kpi ${completedRefunds.length === 1 ? "kpi-good" : completedRefunds.length > 1 ? "kpi-bad" : "kpi-neutral"}`}>
          <span>Completed refunds</span>
          <strong>{completedRefunds.length}</strong>
        </div>
        <div className={`state-kpi ${capturedPayments.length > 0 ? "kpi-warn" : "kpi-neutral"}`}>
          <span>Captured (un-refunded)</span>
          <strong>{capturedPayments.length}</strong>
        </div>
        {pendingRefunds.length > 0 && (
          <div className="state-kpi kpi-warn">
            <span>Pending refunds</span>
            <strong>{pendingRefunds.length}</strong>
          </div>
        )}
        {ticketEntry && (
          <div className="state-kpi kpi-neutral">
            <span>Ticket status</span>
            <strong>{String(ticketEntry.status ?? "—")}</strong>
          </div>
        )}
      </div>
      <details className="state-raw-toggle">
        <summary>Raw JSON</summary>
        <pre>{JSON.stringify(finalState, null, 2)}</pre>
      </details>
    </div>
  );
}

function BaselinePanel({ result }: { result: WorkflowResult }) {
  const bl = result.baseline;
  if (!bl) return null;

  const veraRefunds = useMemo(() => {
    const refunds = result.final_state?.refunds as
      | Record<string, Record<string, unknown>>
      | undefined;
    return refunds
      ? Object.values(refunds).filter((r) => r.status === "completed").length
      : 0;
  }, [result.final_state]);

  const rows = [
    {
      label: "Outcome",
      vera: formatStatus(result.status),
      baseline: formatStatus(bl.status),
      veraClass: result.status.includes("completed") ? "pass-val" : "warn-val",
      baselineClass: bl.status.includes("completed") ? "pass-val" : "warn-val",
    },
    {
      label: "Completed refunds",
      vera: String(veraRefunds),
      baseline: String(bl.completed_refunds),
      veraClass: veraRefunds === 1 ? "pass-val" : veraRefunds > 1 ? "fail-val" : "",
      baselineClass:
        bl.completed_refunds === 1 ? "pass-val" : bl.completed_refunds > 1 ? "fail-val" : "",
    },
    {
      label: "State matched",
      vera: result.final_state_match ? "✓ yes" : "✗ no",
      baseline: bl.final_state_match ? "✓ yes" : "✗ no",
      veraClass: result.final_state_match ? "pass-val" : "fail-val",
      baselineClass: bl.final_state_match ? "pass-val" : "fail-val",
    },
    {
      label: "Audit receipts",
      vera: String(result.audit_receipts.length),
      baseline: String(bl.audit_receipts),
      veraClass: result.audit_receipts.length > 0 ? "pass-val" : "fail-val",
      baselineClass: bl.audit_receipts > 0 ? "pass-val" : "fail-val",
    },
  ];

  return (
    <div className="baseline-panel">
      <div className="baseline-header">
        <GitCompare size={15} />
        VERA vs Baseline (this fixture)
      </div>
      <table className="baseline-table">
        <thead>
          <tr>
            <th>Metric</th>
            <th>VERA</th>
            <th>Baseline</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label}>
              <td className="baseline-label">{r.label}</td>
              <td className={r.veraClass}>{r.vera}</td>
              <td className={r.baselineClass}>{r.baseline}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function WorkflowPane({
  requestText,
  fixtureId,
  result,
  approval,
  isRunning,
  error,
  includeBaseline,
  onRequestTextChange,
  onFixtureChange,
  onRun,
  onApprovalDecide,
  onToggleBaseline,
}: Props) {
  const metrics = useMemo(() => {
    if (!result) return [];
    return [
      { label: "Final state", value: result.final_state_match ? "matched" : "not matched" },
      { label: "Receipts", value: String(result.audit_receipts.length) },
      { label: "Timeline", value: String(result.timeline_events.length) },
      { label: "Transition", value: result.desired_transition_id ?? "none" },
    ];
  }, [result]);

  const mismatchPreview = useMemo(
    () => (result?.mismatch_detail ? JSON.stringify(result.mismatch_detail, null, 2) : ""),
    [result],
  );

  const fixtureDesc = FIXTURE_DESCRIPTIONS[fixtureId];
  const narrative = result ? STATUS_NARRATIVE[result.status] : null;

  return (
    <section className="workspace">
      {/* ── Request ── */}
      <section className="panel request-panel">
        <div className="panel-title">
          <FileText size={18} />
          Request
        </div>
        <label>
          Fixture
          <select value={fixtureId} onChange={(e) => onFixtureChange(e.target.value)}>
            {FIXTURE_IDS.map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        </label>
        {fixtureDesc && (
          <div className="fixture-desc">
            <span className="fixture-label">{fixtureDesc.label}</span>
            <p className="fixture-scenario">{fixtureDesc.scenario}</p>
          </div>
        )}
        <label>
          Customer message
          <textarea value={requestText} onChange={(e) => onRequestTextChange(e.target.value)} />
        </label>
        <label className="baseline-toggle-label">
          <input
            type="checkbox"
            checked={includeBaseline}
            onChange={(e) => onToggleBaseline(e.target.checked)}
          />
          Compare with baseline agent
        </label>
        <button onClick={onRun} disabled={isRunning} type="button">
          {isRunning ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
          {isRunning ? "Running" : "Run VERA"}
        </button>
        {error && <div className="inline-error">{error}</div>}
      </section>

      {/* ── Result ── */}
      <section className="panel result-panel">
        <div className="panel-title">
          <ShieldCheck size={18} />
          Result
        </div>
        {result ? (
          <>
            <div className="result-head">
              <div className={`result-icon ${result.status}`}>{statusIcon(result.status)}</div>
              <div>
                <div className="workflow-id">{result.workflow_id}</div>
                <div className="result-status">{formatStatus(result.status)}</div>
              </div>
            </div>
            <div className="metric-grid">
              {metrics.map((m) => (
                <div className="metric" key={m.label}>
                  <span>{m.label}</span>
                  <strong>{m.value}</strong>
                </div>
              ))}
            </div>
            {result.approval_id && result.status === "approval_pending" && (
              <div className="approval-strip">
                <div>
                  <span>Approval</span>
                  <strong>{approval ? formatStatus(approval.status) : result.approval_id}</strong>
                </div>
                <div className="approval-actions">
                  <button
                    aria-label="Approve"
                    className="icon-button approve"
                    onClick={() => onApprovalDecide("approve")}
                    type="button"
                  >
                    <CheckCircle2 size={18} />
                  </button>
                  <button
                    aria-label="Reject"
                    className="icon-button reject"
                    onClick={() => onApprovalDecide("reject")}
                    type="button"
                  >
                    <XCircle size={18} />
                  </button>
                </div>
              </div>
            )}
            {narrative && <p className="narrative">{narrative}</p>}
            {result.baseline && <BaselinePanel result={result} />}
          </>
        ) : (
          <div className="empty-state">
            <ListChecks size={28} />
            <span>No workflow run selected</span>
          </div>
        )}
      </section>

      {/* ── Timeline ── */}
      <section className="panel timeline-panel">
        <div className="panel-title">
          <Activity size={18} />
          Timeline
        </div>
        <div className="timeline">
          {(result?.timeline_events ?? []).map((event) => (
            <div className="timeline-row" key={event.event_id}>
              <CheckCircle2 className="done-icon" size={18} />
              <div>
                <strong>{formatStatus(event.event_type)}</strong>
                <span>{event.summary}</span>
                <code>{shortHash(event.state_hash)}</code>
              </div>
            </div>
          ))}
          {!result?.timeline_events.length && <p className="muted">No timeline events</p>}
        </div>
      </section>

      {/* ── Audit Receipts ── */}
      <section className="panel audit-panel">
        <div className="panel-title">
          <GitCompare size={18} />
          Audit Receipts
        </div>
        <div className="receipt-list">
          {(result?.audit_receipts ?? []).map((receipt) => (
            <article className="receipt" key={receipt.receipt_id}>
              <header>
                <strong>{receipt.action_id}</strong>
                <span className={`outcome-tag outcome-${receipt.outcome}`}>{receipt.outcome}</span>
              </header>
              <dl>
                <div><dt>Expected</dt><dd>{receipt.intended_transition}</dd></div>
                <div><dt>Observed</dt><dd>{receipt.observed_transition}</dd></div>
                <div>
                  <dt>Hashes</dt>
                  <dd>{shortHash(receipt.pre_state_hash)} {"→"} {shortHash(receipt.post_state_hash)}</dd>
                </div>
              </dl>
            </article>
          ))}
          {!result?.audit_receipts.length && <p className="muted">No receipts</p>}
        </div>
      </section>

      {/* ── State ── */}
      <section className="panel state-panel">
        <div className="panel-title">
          <GitCompare size={18} />
          State
        </div>
        {mismatchPreview && (
          <div className="state-block">
            <div className="state-block-title">Mismatch</div>
            <pre>{mismatchPreview}</pre>
          </div>
        )}
        <div className="state-block">
          <div className="state-block-title">Final State</div>
          <StateHighlight finalState={result?.final_state ?? null} />
        </div>
      </section>
    </section>
  );
}
