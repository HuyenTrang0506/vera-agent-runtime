import { BarChart2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { BenchmarkPane } from "./components/BenchmarkPane";
import { WorkflowPane } from "./components/WorkflowPane";
import { DEFAULT_REQUEST_TEXT, FIXTURE_IDS } from "./constants/fixtures";
import { ApprovalRecord, EvalResult, WorkflowResult } from "./types";
import { formatStatus } from "./utils/format";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type Tab = "workflow" | "benchmark";

function App() {
  const [tab, setTab] = useState<Tab>("workflow");

  // workflow state
  const [requestText, setRequestText] = useState(DEFAULT_REQUEST_TEXT);
  const [fixtureId, setFixtureId] = useState<string>(FIXTURE_IDS[0]);
  const [result, setResult] = useState<WorkflowResult | null>(null);
  const [approval, setApproval] = useState<ApprovalRecord | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [includeBaseline, setIncludeBaseline] = useState(false);

  // eval state
  const [evalResult, setEvalResult] = useState<EvalResult | null>(null);
  const [isEvalRunning, setIsEvalRunning] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  // pre-populate benchmark with last run on mount
  useEffect(() => {
    fetch(`${API_BASE}/evaluation/latest`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d) setEvalResult(d as EvalResult); })
      .catch(() => {});
  }, []);

  async function runWorkflow() {
    setIsRunning(true);
    setError(null);
    setResult(null);
    setApproval(null);
    try {
      const res = await fetch(`${API_BASE}/workflows/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: "customer_support",
          request_text: requestText,
          fixture_id: fixtureId,
          operator_id: "op_demo",
          include_baseline: includeBaseline,
        }),
      });
      if (!res.ok) throw new Error(`Workflow request failed with ${res.status}`);
      setResult((await res.json()) as WorkflowResult);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reach VERA API.");
    } finally {
      setIsRunning(false);
    }
  }

  async function runBenchmark() {
    setIsEvalRunning(true);
    setEvalError(null);
    setEvalResult(null);
    try {
      const res = await fetch(`${API_BASE}/evaluation/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repeated_runs: 2, include_baseline: true }),
      });
      if (!res.ok) throw new Error(`Evaluation failed with ${res.status}`);
      setEvalResult((await res.json()) as EvalResult);
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : "Could not reach VERA API.");
    } finally {
      setIsEvalRunning(false);
    }
  }

  async function decideApproval(decision: "approve" | "reject") {
    if (!result?.approval_id) return;
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/approvals/${result.approval_id}/${decision}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          decided_by: "manager_demo",
          comment: decision === "approve" ? "Approved in demo console." : "Rejected in demo console.",
        }),
      });
      if (!res.ok) throw new Error(`Approval request failed with ${res.status}`);
      setApproval((await res.json()) as ApprovalRecord);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not record approval decision.");
    }
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Qwen Enterprise Autopilot</p>
          <h1>VERA Operator Console</h1>
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

      {tab === "workflow" && (
        <WorkflowPane
          requestText={requestText}
          fixtureId={fixtureId}
          result={result}
          approval={approval}
          isRunning={isRunning}
          error={error}
          includeBaseline={includeBaseline}
          onRequestTextChange={setRequestText}
          onFixtureChange={setFixtureId}
          onRun={runWorkflow}
          onApprovalDecide={decideApproval}
          onToggleBaseline={setIncludeBaseline}
        />
      )}

      {tab === "benchmark" && (
        <BenchmarkPane
          evalResult={evalResult}
          isRunning={isEvalRunning}
          error={evalError}
          onRun={runBenchmark}
        />
      )}
    </main>
  );
}

export default App;
