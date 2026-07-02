import { Activity, CheckCircle2, FileText, Play, ShieldCheck } from "lucide-react";
import { useMemo, useState } from "react";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type WorkflowResult = {
  workflow_id: string;
  status: string;
  desired_transition_id: string | null;
  policy_decision: string | null;
  final_state_match: boolean;
  audit_receipt_ids: string[];
  message?: string | null;
};

const defaultRequest = "I was charged twice for order A102. Refund me now.";

function App() {
  const [requestText, setRequestText] = useState(defaultRequest);
  const [fixtureId, setFixtureId] = useState("support_refund_happy_001");
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const timeline = useMemo(
    () => [
      { label: "Extract intent", state: result ? "done" : "idle" },
      { label: "Check policy", state: result ? "done" : "idle" },
      { label: "Execute gated action", state: result ? "done" : "idle" },
      { label: "Validate final state", state: result ? "done" : "idle" },
      { label: "Write audit receipt", state: result ? "done" : "idle" },
    ],
    [result],
  );

  async function runWorkflow() {
    setIsRunning(true);
    setResult(null);
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
      const payload = (await response.json()) as WorkflowResult;
      setResult(payload);
    } catch {
      setResult({
        workflow_id: "wf_ui_error",
        status: "failed_safe",
        desired_transition_id: null,
        policy_decision: null,
        final_state_match: false,
        audit_receipt_ids: [],
        message: "Could not reach SafeFlow API.",
      });
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Qwen Enterprise Autopilot</p>
          <h1>SafeFlow Operator Console</h1>
        </div>
        <div className="status-pill">
          <ShieldCheck size={18} />
          P0 support workflow
        </div>
      </section>

      <section className="workspace">
        <div className="panel request-panel">
          <div className="panel-title">
            <FileText size={18} />
            Request
          </div>
          <label>
            Fixture
            <input value={fixtureId} onChange={(event) => setFixtureId(event.target.value)} />
          </label>
          <label>
            Customer message
            <textarea value={requestText} onChange={(event) => setRequestText(event.target.value)} />
          </label>
          <button onClick={runWorkflow} disabled={isRunning}>
            <Play size={18} />
            {isRunning ? "Running" : "Run SafeFlow"}
          </button>
        </div>

        <div className="panel timeline-panel">
          <div className="panel-title">
            <Activity size={18} />
            Timeline
          </div>
          <div className="timeline">
            {timeline.map((item) => (
              <div className="timeline-row" key={item.label}>
                <CheckCircle2 className={item.state === "done" ? "done-icon" : "idle-icon"} size={18} />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="panel result-panel">
          <div className="panel-title">
            <ShieldCheck size={18} />
            Result
          </div>
          {result ? (
            <dl>
              <div>
                <dt>Workflow</dt>
                <dd>{result.workflow_id}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{result.status}</dd>
              </div>
              <div>
                <dt>Transition</dt>
                <dd>{result.desired_transition_id ?? "none"}</dd>
              </div>
              <div>
                <dt>Policy</dt>
                <dd>{result.policy_decision ?? "none"}</dd>
              </div>
              <div>
                <dt>Final state</dt>
                <dd>{result.final_state_match ? "matched" : "not matched"}</dd>
              </div>
            </dl>
          ) : (
            <p className="muted">Run a fixture to inspect workflow state, policy, and audit output.</p>
          )}
        </div>
      </section>
    </main>
  );
}

export default App;

