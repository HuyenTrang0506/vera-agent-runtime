import { Activity, BarChart2, CheckCircle2, ListChecks, Play, RefreshCw, XCircle } from "lucide-react";
import { EvalResult } from "../types";
import { formatStatus, pct } from "../utils/format";

const P0_METRIC_SPECS = [
  { key: "business_task_success_rate" as const, label: "Business success", target: "≥ 80%", threshold: 0.8, isRate: true },
  { key: "final_state_exact_match_rate" as const, label: "Final state match", target: "≥ 80%", threshold: 0.8, isRate: true },
  { key: "desired_transition_match_rate" as const, label: "Desired transition match", target: "≥ 85%", threshold: 0.85, isRate: true },
  { key: "audit_completeness_rate" as const, label: "Audit completeness", target: "≥ 95%", threshold: 0.95, isRate: true },
  { key: "approval_recall" as const, label: "Approval recall", target: "100%", threshold: 1.0, isRate: true },
  { key: "rejection_compliance_rate" as const, label: "Rejection compliance", target: "100%", threshold: 1.0, isRate: true },
  { key: "duplicate_refund_count" as const, label: "Duplicate refunds", target: "0", threshold: 0, isRate: false },
  { key: "forbidden_transition_count" as const, label: "Forbidden transitions", target: "0", threshold: 0, isRate: false },
] as const;

type Props = {
  evalResult: EvalResult | null;
  isRunning: boolean;
  error: string | null;
  onRun: () => void;
};

export function BenchmarkPane({ evalResult, isRunning, error, onRun }: Props) {
  return (
    <section className="dashboard">
      <section className="panel dashboard-run-panel">
        <div className="panel-title">
          <BarChart2 size={18} />
          Benchmark Evaluation
        </div>
        <p className="muted-sm">Run SafeFlow on all benchmark cases and view aggregate metrics.</p>
        <button onClick={onRun} disabled={isRunning} type="button" className="btn-bench">
          {isRunning ? <RefreshCw className="spin" size={18} /> : <Play size={18} />}
          {isRunning ? "Running benchmark…" : "Run benchmark"}
        </button>
        {error && <div className="inline-error">{error}</div>}
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
              {P0_METRIC_SPECS.map((spec) => {
                const raw = evalResult.metrics[spec.key];
                const ok = spec.isRate ? (raw as number) >= spec.threshold : (raw as number) === spec.threshold;
                const display = spec.isRate ? pct(raw as number) : String(raw);
                return (
                  <div className={`eval-metric${ok ? " pass" : " fail"}`} key={spec.key}>
                    <span>{spec.label}</span>
                    <strong>{display}</strong>
                    <em>target {spec.target}</em>
                  </div>
                );
              })}
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
                      <td>
                        {t.final_state_match
                          ? <CheckCircle2 size={14} className="done-icon" />
                          : <XCircle size={14} className="fail-icon" />}
                      </td>
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
  );
}
