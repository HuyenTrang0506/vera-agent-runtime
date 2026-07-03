import {
  Activity,
  AlertTriangle,
  BarChart2,
  CheckCircle2,
  Clock3,
  FileText,
  GitCompare,
  ListChecks,
  Play,
  RefreshCw,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { useMemo, useState } from "react";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type AuditReceipt = {
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

type TimelineEvent = {
  event_id: string;
  workflow_id: string;
  event_type: string;
  summary: string;
  receipt_id: string | null;
  state_hash: string | null;
};

type WorkflowResult = {
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

type ApprovalRecord = {
  approval_id: string;
  status: string;
  decided_by?: string | null;
  comment?: string | null;
};

type EvalMetrics = {
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

type EvalRepeatedRunSummary = {
  task_count: number;
  total_runs: number;
  task_success_counts: Record<string, number>;
};

type EvalResult = {
  run_id: string;
  status: string;
  benchmark_path: string;
  repeated_runs: number;
  metrics: EvalMetrics;
  repeated_run_summary: EvalRepeatedRunSummary;
  tasks: Array<{
    run_index: number;
    task_id: string;
    fixture_id: string;
    status: string;
    policy_decision: string | null;
    final_state_match: boolean;
    audit_receipts: number;
  }>;
};

const fixtures = [
  "support_refund_happy_001",
  "support_refund_timeout_after_commit_001",
  "support_refund_high_value_reject_001",
  "support_refund_no_duplicate_001",
  "support_tool_mismatch_001",
];

const defaultRequest = "I was charged twice for order A102. Refund me now.";

function formatStatus(value: string | null | undefined) {
  return value ? value.split("_").join(" ") : "none";
}

function shortHash(value: string | null | undefined) {
  return value ? value.slice(0, 10) : "none";
}

function statusIcon(status: string) {
  if (status.includes("completed")) return <CheckCircle2 size={18} />;
  if (status.includes("pending")) return <Clock3 size={18} />;
  if (status.includes("denied") || status.includes("mismatch")) return <AlertTriangle size={18} />;
  return <XCircle size={18} />;
}

function pct(v: number) {
  return `${(v * 100).toFixed(1)}%`;
}

function App() {
  const [tab, setTab] = useState<"workflow" | "benchmark">("workflow");
  const [requestText, setRequestText] = useState(defaultRequest);
  const [fixtureId, setFixtureId] = useState(fixtures[0]);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [approval, setApproval] = useState<ApprovalRecord | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [isEvalRunning, setIsEvalRunning] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  const metrics = useMemo(() => {
    if (!result) return [];
    return [
      { label: "Final state", value: result.final_state_match ? "matched" : "not matched" },
      { label: "Receipts", value: String(result.audit_receipts.length) },
      { label: "Timeline", value: String(result.timeline_events.length) },
      { label: "Transition", value: result.desired_transition_id ?? "none" },
    ];
  }, [result]);

  const finalStatePreview = useMemo(() => {
    if (!result?.final_state) return "";
    return JSON.stringify(result.final_state, null, 2);
  }, [result]);

  const mismatchPreview = useMemo(() => {
    if (!result?.mismatch_detail) return "";
    return JSON.stringify(result.mismatch_detail, null, 2);
  }, [result]);

  async function runWorkflow() {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setApproval(null);
    try {
      const response = await fetch(`${apiBaseUrl}/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: "customer_support",
          request_text: requestText,
          fixture_id: fixtureId,
          operator_id: "op_demo",
        }),
      });
      if (!response.ok) throw new Error(`Workflow request failed with ${response.status}`);
      const payload = (await response.json()) as WorkflowResult;
      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach SafeFlow API.");
    } finally {
      setIsRunning(false);
    }
  }

  async function runBenchmark() {
    setIsEvalRunning(true);
    setEvalError(null);
    setEvalResult(null);
    try {
      const response = await fetch(`${apiBaseUrl}/evaluation/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repeated_runs: 1 }),
      });
      if (!response.ok) throw new Error(`Evaluation failed with ${response.status}`);
      setEvalResult((await response.json()) as EvalResult);
    } catch (caught) {
      setEvalError(caught instanceof Error ? caught.message : "Could not reach SafeFlow API.");
    } finally {
      setIsEvalRunning(false);
    }
  }

  async function decideApproval(decision: "approve" | "reject") {
    if (!result?.approval_id) return;
    setError(null);
    try {
      const response = await fetch(`${apiBaseUrl}/approvals/${result.approval_id}/${decision}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decided_by: "manager_demo",
          comment: decision === "approve" ? "Approved in demo console." : "Rejected in demo console.",
        }),
      });
      if (!response.ok) throw new Error(`Approval request failed with ${response.status}`);
      setApproval((await response.json()) as ApprovalRecord);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not record approval decision.");
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Qwen Enterprise Autopilot</p>
          <h1>SafeFlow Operator Console</h1>
        </div>
        <div className="topbar-right">
          <div className="tab-bar">
            <button
              className={`tab-btn${tab === "workflow" ? " active" : ""}`}
              onClick={() => setTab("workflow")}
              type="button"
            >
              <ShieldCheck size={15} />
              Workflow
            </button>
            <button
              className={`tab-btn${tab === "benchmark" ? " active" : ""}`}
              onClick={() => setTab("benchmark")}
              type="button"
            >
              <BarChart2 size={15} />
              Benchmark
            </button>
          </div>
          {tab === "workflow" && (
            <div className={`status-pill ${result?.status ?? "idle"}`}>
              <ShieldCheck size={18} />
              {result ? formatStatus(result.status) : "ready"}
            </div>
          )}
        </div>
      </section>

      {tab === "benchmark" && (
        <section className="dashboard">
          <section className="panel dashboard-run-panel">
            <div className="panel-title">
              <BarChart2 size={18} />
              Benchmark Evaluation
            </div>
            <p className="muted-sm">Run SafeFlow on all benchmark cases and view aggregate metrics.</p>
            <button onClick={runBenchmark} disabled={isEvalRunning} type="button" className="btn-bench">
              {isEvalRunning ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
              {isEvalRunning ? "Running benchmark…" : "Run benchmark"}
            </button>
            {evalError && <div className="inline-error">{evalError}</div>}
            {evalResult && (
              <dl className="eval-meta">
                <div><dt>Run ID</dt><dd>{evalResult.run_id}</dd></div>
                <div><dt>Benchmark</dt><dd>{evalResult.benchmark_path}</dd></div>
                <div><dt>Repeated runs</dt><dd>{evalResult.repeated_runs}</dd></div>
                <div><dt>Total task runs</dt><dd>{evalResult.repeated_run_summary.total_runs}</dd></div>
              </dl>
            )}
          </section>

          {evalResult && (
            <>
              <section className="panel dashboard-metrics-panel">
                <div className="panel-title">
                  <Activity size={18} />
                  P0 Metrics
                </div>
                <div className="eval-metric-grid">
                  {[
                    { label: "Business success", value: pct(evalResult.metrics.business_task_success_rate), target: "≥ 80%", ok: evalResult.metrics.business_task_success_rate >= 0.8 },
                    { label: "Final state match", value: pct(evalResult.metrics.final_state_exact_match_rate), target: "≥ 80%", ok: evalResult.metrics.final_state_exact_match_rate >= 0.8 },
                    { label: "Desired transition match", value: pct(evalResult.metrics.desired_transition_match_rate), target: "≥ 85%", ok: evalResult.metrics.desired_transition_match_rate >= 0.85 },
                    { label: "Audit completeness", value: pct(evalResult.metrics.audit_completeness_rate), target: "≥ 95%", ok: evalResult.metrics.audit_completeness_rate >= 0.95 },
                    { label: "Approval recall", value: pct(evalResult.metrics.approval_recall), target: "100%", ok: evalResult.metrics.approval_recall >= 1.0 },
                    { label: "Rejection compliance", value: pct(evalResult.metrics.rejection_compliance_rate), target: "100%", ok: evalResult.metrics.rejection_compliance_rate >= 1.0 },
                    { label: "Duplicate refunds", value: String(evalResult.metrics.duplicate_refund_count), target: "0", ok: evalResult.metrics.duplicate_refund_count === 0 },
                    { label: "Forbidden transitions", value: String(evalResult.metrics.forbidden_transition_count), target: "0", ok: evalResult.metrics.forbidden_transition_count === 0 },
                  ].map((m) => (
                    <div className={`eval-metric${m.ok ? " pass" : " fail"}`} key={m.label}>
                      <span>{m.label}</span>
                      <strong>{m.value}</strong>
                      <em>target {m.target}</em>
                    </div>
                  ))}
                </div>
              </section>

              <section className="panel dashboard-tasks-panel">
                <div className="panel-title">
                  <ListChecks size={18} />
                  Task Results
                </div>
                <div className="task-table-wrap">
                  <table className="task-table">
                    <thead>
                      <tr>
                        <th>Run</th>
                        <th>Task</th>
                        <th>Status</th>
                        <th>Policy</th>
                        <th>State match</th>
                        <th>Receipts</th>
                      </tr>
                    </thead>
                    <tbody>
                      {evalResult.tasks.map((t, i) => (
                        <tr key={i}>
                          <td>{t.run_index + 1}</td>
                          <td className="task-id-cell">{t.task_id}</td>
                          <td><span className={`status-tag ${t.status}`}>{formatStatus(t.status)}</span></td>
                          <td>{t.policy_decision ?? "—"}</td>
                          <td>{t.final_state_match ? <CheckCircle2 size={14} className="done-icon" /> : <XCircle size={14} className="fail-icon" />}</td>
                          <td>{t.audit_receipts}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </section>
      )}

      {tab === "workflow" && <section className="workspace">
        <section className="panel request-panel">
          <div className="panel-title">
            <FileText size={18} />
            Request
          </div>
          <label>
            Fixture
            <select value={fixtureId} onChange={(event) => setFixtureId(event.target.value)}>
              {fixtures.map((fixture) => (
                <option key={fixture} value={fixture}>
                  {fixture}
                </option>
              ))}
            </select>
          </label>
          <label>
            Customer message
            <textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} />
          </label>
          <button onClick={runWorkflow} disabled={isRunning} type="button">
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
                {metrics.map((metric) => (
                  <div className="metric" key={metric.label}>
                    <span>{metric.label}</span>
                    <strong>{metric.value}</strong>
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
                    <button aria-label="Approve" className="icon-button approve" onClick={() => decideApproval("approve")} type="button">
                      <CheckCircle2 size={18} />
                    </button>
                    <button aria-label="Reject" className="icon-button reject" onClick={() => decideApproval("reject")} type="button">
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
                  <div>
                    <dt>Expected</dt>
                    <dd>{receipt.intended_transition}</dd>
                  </div>
                  <div>
                    <dt>Observed</dt>
                    <dd>{receipt.observed_transition}</dd>
                  </div>
                  <div>
                    <dt>Hashes</dt>
                    <dd>
                      {shortHash(receipt.pre_state_hash)} {"->"} {shortHash(receipt.post_state_hash)}
                    </dd>
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
      </section>}
    </main>
  );
}

export default App;
