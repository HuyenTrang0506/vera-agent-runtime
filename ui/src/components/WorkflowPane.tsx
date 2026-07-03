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
import { FIXTURE_IDS } from "../constants/fixtures";
import { ApprovalRecord, WorkflowResult } from "../types";
import { formatStatus, shortHash, statusIcon } from "../utils/format";

type Props = {
  requestText: string;
  fixtureId: string;
  result: WorkflowResult | null;
  approval: ApprovalRecord | null;
  isRunning: boolean;
  error: string | null;
  onRequestTextChange: (v: string) => void;
  onFixtureChange: (v: string) => void;
  onRun: () => void;
  onApprovalDecide: (decision: "approve" | "reject") => void;
};

export function WorkflowPane({
  requestText,
  fixtureId,
  result,
  approval,
  isRunning,
  error,
  onRequestTextChange,
  onFixtureChange,
  onRun,
  onApprovalDecide,
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

  const finalStatePreview = useMemo(
    () => (result?.final_state ? JSON.stringify(result.final_state, null, 2) : ""),
    [result],
  );

  const mismatchPreview = useMemo(
    () => (result?.mismatch_detail ? JSON.stringify(result.mismatch_detail, null, 2) : ""),
    [result],
  );

  return (
    <section className="workspace">
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
        <label>
          Customer message
          <textarea value={requestText} onChange={(e) => onRequestTextChange(e.target.value)} />
        </label>
        <button onClick={onRun} disabled={isRunning} type="button">
          {isRunning ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
          {isRunning ? "Running" : "Run SafeFlow"}
        </button>
        {error && <div className="inline-error">{error}</div>}
      </section>

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
            {result.message && <p className="message">{result.message}</p>}
          </>
        ) : (
          <div className="empty-state">
            <ListChecks size={28} />
            <span>No workflow run selected</span>
          </div>
        )}
      </section>

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
                <span>{receipt.outcome}</span>
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
          <pre>{finalStatePreview || "{}"}</pre>
        </div>
      </section>
    </section>
  );
}
