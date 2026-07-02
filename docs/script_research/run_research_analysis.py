#!/usr/bin/env python3
"""Run an evidence-first research analysis for Milestone A.

This script intentionally stops before product ideation. It collects GitHub
issues from major AI-agent repositories, classifies recurring pain points, and
turns them into research gaps that can be reviewed before any final hackathon
idea is selected.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DOC_DIR = ROOT / "docs"
OUT_DATA = DATA_DIR / "analysis"
OUT_DOCS = DOC_DIR / "analysis"
USER_AGENT = "qwen-practice-research-analysis"


TARGET_REPOS = [
    ("langchain-ai/langgraph", "LangGraph"),
    ("microsoft/autogen", "Microsoft AutoGen"),
    ("crewAIInc/crewAI", "CrewAI"),
    ("letta-ai/letta", "Letta"),
    ("mem0ai/mem0", "Mem0"),
    ("All-Hands-AI/OpenHands", "OpenHands"),
    ("browser-use/browser-use", "Browser Use"),
    ("huggingface/smolagents", "SmolAgents"),
    ("openai/openai-agents-python", "OpenAI Agents SDK"),
    ("run-llama/llama_index", "LlamaIndex"),
    ("langgenius/dify", "Dify"),
    ("QwenLM/Qwen-Agent", "Qwen-Agent"),
]

ISSUE_PAGES_PER_REPO = 2


CATEGORIES = {
    "Memory": [
        "memory",
        "remember",
        "forget",
        "retrieval",
        "recall",
        "embedding",
        "vector",
        "context store",
        "persistent",
    ],
    "Planning": [
        "plan",
        "planning",
        "decompose",
        "subtask",
        "step",
        "reasoning",
        "loop",
        "terminate",
        "termination",
    ],
    "Tool Calling": [
        "tool",
        "function",
        "schema",
        "argument",
        "json",
        "call",
        "api",
        "browser",
        "code interpreter",
    ],
    "Coordination": [
        "multi-agent",
        "multi agent",
        "crew",
        "team",
        "handoff",
        "delegate",
        "manager",
        "worker",
        "conversation",
    ],
    "Cost": ["cost", "token", "expensive", "billing", "rate limit", "quota"],
    "Latency": ["slow", "latency", "timeout", "hang", "performance", "speed"],
    "Evaluation": [
        "eval",
        "evaluation",
        "benchmark",
        "trace",
        "observability",
        "metric",
        "test",
    ],
    "Hallucination": [
        "hallucination",
        "hallucinate",
        "wrong",
        "incorrect",
        "fabricate",
        "invalid",
        "nonsense",
    ],
    "Human-in-the-loop": [
        "human",
        "approval",
        "interrupt",
        "confirm",
        "review",
        "manual",
        "permission",
    ],
    "Context": [
        "context",
        "window",
        "prompt",
        "history",
        "long context",
        "truncat",
        "summar",
    ],
    "Long-term tasks": [
        "long running",
        "long-running",
        "resume",
        "checkpoint",
        "state",
        "durable",
        "crash",
        "recover",
    ],
    "Workflow": [
        "workflow",
        "graph",
        "node",
        "edge",
        "pipeline",
        "flow",
        "trigger",
    ],
    "Reliability": [
        "reliable",
        "reliability",
        "failed",
        "failure",
        "bug",
        "error",
        "exception",
        "crash",
        "unstable",
        "retry",
    ],
    "Safety": [
        "safety",
        "guardrail",
        "permission",
        "sandbox",
        "security",
        "injection",
        "leak",
    ],
}


PATTERNS = [
    {
        "name": "Memory pollution and stale state",
        "categories": ["Memory", "Context", "Reliability"],
        "current_solution": "Vector/graph memory layers, summarization, explicit memory blocks, and application-specific write policies.",
        "remaining_gap": "Frameworks rarely estimate whether a memory will improve a future decision before writing or retrieving it.",
        "question": "Can agent memory be gated by predicted decision impact instead of semantic similarity alone?",
        "contribution": "A memory controller that scores candidate memories by expected action impact, contradiction risk, and freshness.",
        "benchmark": "MemoryBank, LoCoMo-style long conversation tasks, synthetic conflicting-memory task suites.",
    },
    {
        "name": "Tool loops and failed termination",
        "categories": ["Tool Calling", "Planning", "Reliability", "Cost"],
        "current_solution": "Max-iteration caps, stop conditions, retries, traces, and guardrails.",
        "remaining_gap": "Most systems stop loops mechanically rather than diagnosing why the same action keeps recurring.",
        "question": "Can agents detect non-progress in tool-use trajectories before cost explodes?",
        "contribution": "A trajectory monitor that compares action novelty, state delta, and goal progress to trigger repair or escalation.",
        "benchmark": "WebArena/MiniWoB-style browser tasks, tool-use regression suites, coding-agent trajectories.",
    },
    {
        "name": "Poor task decomposition",
        "categories": ["Planning", "Workflow", "Reliability"],
        "current_solution": "Planner prompts, graph nodes, task lists, and hierarchical managers.",
        "remaining_gap": "Decomposition quality is rarely evaluated before execution, so weak plans consume tools and context.",
        "question": "Can task decompositions be checked for dependency completeness before execution?",
        "contribution": "A plan verifier that validates preconditions, dependencies, and observability for each subtask.",
        "benchmark": "Agent planning benchmarks, SWE-bench subtasks, workflow execution simulations.",
    },
    {
        "name": "Wrong tool selection and schema mismatch",
        "categories": ["Tool Calling", "Hallucination", "Reliability"],
        "current_solution": "Better tool descriptions, JSON schema validation, retries, and model-native function calling.",
        "remaining_gap": "Agents often choose plausible tools without causal evidence that the tool can change the task state.",
        "question": "Can tool selection be conditioned on expected state transition rather than description matching?",
        "contribution": "A tool router that predicts required state change and selects tools by transition affordance.",
        "benchmark": "ToolBench, API-Bank, τ-bench, custom schema-conflict tasks.",
    },
    {
        "name": "Multi-agent disagreement and deadlock",
        "categories": ["Coordination", "Planning", "Evaluation", "Reliability"],
        "current_solution": "Manager-worker roles, round-robin chat, voting, critic agents, and handoffs.",
        "remaining_gap": "Multi-agent systems often lack explicit conflict semantics and accountability for final decisions.",
        "question": "Can multi-agent coordination use explicit disagreement contracts instead of free-form debate?",
        "contribution": "A coordination protocol that records claims, evidence, objections, and resolution responsibility.",
        "benchmark": "Collaborative QA, multi-agent coding tasks, negotiation and debate datasets.",
    },
    {
        "name": "Context explosion",
        "categories": ["Context", "Memory", "Cost", "Latency"],
        "current_solution": "Summaries, retrieval, context compression, and larger context windows.",
        "remaining_gap": "Compression is often relevance-based, not decision-sensitive or risk-aware.",
        "question": "Can context pruning preserve action-critical evidence while discarding conversational bulk?",
        "contribution": "A context budgeter that protects facts tied to pending decisions, tool constraints, and unresolved claims.",
        "benchmark": "LongBench-agent variants, long-context RAG tasks, multi-turn workflow tasks.",
    },
    {
        "name": "Recovery failure after bad actions",
        "categories": ["Long-term tasks", "Reliability", "Workflow", "Tool Calling"],
        "current_solution": "Retries, checkpoints, human approval, and manual rollback.",
        "remaining_gap": "Agents often retry without identifying the smallest recoverable state boundary.",
        "question": "Can agents learn recoverable checkpoints around irreversible or high-risk tool actions?",
        "contribution": "A rollback-aware executor that marks side effects, recovery cost, and safe retry boundaries.",
        "benchmark": "SWE-bench trajectories, browser transaction simulations, sandboxed tool workflows.",
    },
    {
        "name": "Evaluation mismatch",
        "categories": ["Evaluation", "Reliability", "Workflow"],
        "current_solution": "Traces, unit tests, benchmark tasks, human review, and LLM-as-judge.",
        "remaining_gap": "Framework-level metrics often measure execution traces but not whether user intent was satisfied robustly.",
        "question": "Can agent evaluation combine task success, recoverability, and user-intervention cost into one score?",
        "contribution": "An evaluation rubric and harness for agent workflows with explicit failure-mode accounting.",
        "benchmark": "τ-bench, SWE-bench, WebArena, custom human-intervention simulations.",
    },
    {
        "name": "Human approval bottlenecks",
        "categories": ["Human-in-the-loop", "Safety", "Latency", "Workflow"],
        "current_solution": "Interrupts, approval steps, permissions, and manual checkpoints.",
        "remaining_gap": "Human review is treated as a binary gate rather than a scarce resource to allocate by risk.",
        "question": "Can agents request human approval only when predicted consequence risk exceeds autonomy benefit?",
        "contribution": "A risk-budgeted approval policy that ranks actions by reversibility, cost, and uncertainty.",
        "benchmark": "Workflow simulations with approval cost, browser automation tasks, enterprise-agent scenarios.",
    },
    {
        "name": "Prompt sensitivity and hidden assumptions",
        "categories": ["Hallucination", "Planning", "Evaluation", "Reliability"],
        "current_solution": "Prompt templates, examples, validators, guardrails, and test suites.",
        "remaining_gap": "Prompts encode assumptions that are rarely surfaced, tested, or updated as tasks change.",
        "question": "Can agent prompts be decomposed into testable behavioral assumptions?",
        "contribution": "An assumption miner that extracts prompt claims and runs counterfactual tests against agent behavior.",
        "benchmark": "Prompt perturbation suites, agent regression tests, multi-model prompt robustness tasks.",
    },
]


ASSUMPTIONS = [
    ("Semantic similarity implies relevance", "Memory and RAG systems often retrieve by embedding closeness.", "Semantically close memories may be stale, false, low-impact, or harmful to the next action."),
    ("More context improves reasoning", "Long-context agents often append more history, traces, and retrieved data.", "Extra context can increase cost, latency, distraction, and prompt conflict."),
    ("Role assignment creates useful collaboration", "Multi-agent frameworks define specialist roles such as planner, executor, critic, and manager.", "Roles can duplicate work, amplify errors, or create deadlock without explicit conflict resolution."),
    ("Retries improve reliability", "Tool-use systems often retry failed calls or malformed outputs.", "Retries can repeat the same failure if the agent does not diagnose non-progress."),
    ("Tool descriptions are enough for tool choice", "Agents select tools from natural-language descriptions and schemas.", "Descriptions do not guarantee the selected tool can cause the needed state transition."),
    ("A valid JSON/function call is a correct action", "SDKs validate schema conformance.", "Schema validity says little about whether the call helps the task."),
    ("Human approval increases safety", "Frameworks add interrupts and approval gates.", "Too many approvals create bottlenecks; too few miss consequential actions."),
    ("Graph structure guarantees workflow control", "Graph frameworks expose explicit states and transitions.", "A graph can still encode weak plans, poor recovery paths, or bad state updates."),
    ("Agent traces are sufficient for evaluation", "Many frameworks expose tracing and observability.", "Traces explain what happened but do not alone score task success, user burden, or recoverability."),
    ("Planning before acting is enough", "Planner-executor designs generate a plan before tool use.", "Plans may be incomplete, unobservable, or invalid under changing tool feedback."),
]


def github_get(path: str):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"https://api.github.com{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8")), response.headers
    except urllib.error.HTTPError as exc:
        print(f"GitHub API error {exc.code} for {path}", file=sys.stderr)
    except Exception as exc:
        print(f"GitHub API error for {path}: {exc}", file=sys.stderr)
    return None, {}


def clean(text: str | None, limit: int = 1200) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def classify(text: str) -> list[str]:
    lower = text.lower()
    scores = []
    for category, keywords in CATEGORIES.items():
        score = sum(1 for keyword in keywords if keyword in lower)
        if score:
            scores.append((score, category))
    scores.sort(reverse=True)
    return [category for _score, category in scores[:3]] or ["Uncategorized"]


def collect_issues() -> list[dict]:
    rows = []
    for repo, framework in TARGET_REPOS:
        print(f"Collecting issues from {repo}...", file=sys.stderr)
        encoded = urllib.parse.quote(repo, safe="/")
        for page in range(1, ISSUE_PAGES_PER_REPO + 1):
            data, _headers = github_get(
                f"/repos/{encoded}/issues?state=all&sort=updated&direction=desc&per_page=100&page={page}"
            )
            if not isinstance(data, list):
                continue
            for issue in data:
                if "pull_request" in issue:
                    continue
                text = f"{issue.get('title', '')} {issue.get('body', '')}"
                categories = classify(text)
                labels = "; ".join(label.get("name", "") for label in issue.get("labels", []))
                reactions = issue.get("reactions") or {}
                reaction_count = sum(
                    int(reactions.get(key, 0))
                    for key in ["+1", "-1", "laugh", "hooray", "confused", "heart", "rocket", "eyes"]
                )
                rows.append(
                    {
                        "source": "GitHub Issues",
                        "url": issue.get("html_url", ""),
                        "date": issue.get("created_at", ""),
                        "updated_at": issue.get("updated_at", ""),
                        "repository": repo,
                        "framework": framework,
                        "issue_number": issue.get("number", ""),
                        "issue_title": clean(issue.get("title", ""), 300),
                        "issue_body": clean(issue.get("body", ""), 1600),
                        "labels": labels,
                        "number_of_comments": issue.get("comments", 0),
                        "reactions": reaction_count,
                        "whether_resolved": "yes" if issue.get("state") == "closed" else "no",
                        "category": "; ".join(categories),
                        "state": issue.get("state", ""),
                    }
                )
            time.sleep(0.35)
    rows.sort(
        key=lambda row: (
            int(row["number_of_comments"] or 0) + int(row["reactions"] or 0),
            row["updated_at"],
        ),
        reverse=True,
    )
    return rows


def write_issues(rows: list[dict]) -> None:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "url",
        "date",
        "updated_at",
        "repository",
        "framework",
        "issue_number",
        "issue_title",
        "issue_body",
        "labels",
        "number_of_comments",
        "reactions",
        "whether_resolved",
        "category",
        "state",
    ]
    with (OUT_DATA / "issues_database.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evidence_counts(rows: list[dict]) -> tuple[Counter, dict[str, list[dict]]]:
    counts = Counter()
    examples = defaultdict(list)
    for row in rows:
        cats = [cat.strip() for cat in row["category"].split(";")]
        for cat in cats:
            counts[cat] += 1
            if len(examples[cat]) < 5:
                examples[cat].append(row)
    return counts, examples


def pattern_score(pattern: dict, counts: Counter) -> int:
    return sum(counts.get(category, 0) for category in pattern["categories"])


def write_failure_patterns(rows: list[dict], counts: Counter, examples: dict[str, list[dict]]) -> None:
    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Failure Patterns",
        "",
        f"Generated on: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        f"Evidence base: {len(rows)} recent GitHub issues across {len(TARGET_REPOS)} agent repositories.",
        "",
    ]
    for pattern in sorted(PATTERNS, key=lambda item: pattern_score(item, counts), reverse=True):
        related_count = pattern_score(pattern, counts)
        lines.extend(
            [
                f"## {pattern['name']}",
                "",
                f"Problem: {pattern['remaining_gap']}",
                "",
                f"Frequency signal: {related_count} category hits across {', '.join(pattern['categories'])}.",
                "",
                f"Current solution: {pattern['current_solution']}",
                "",
                f"Remaining gap: {pattern['remaining_gap']}",
                "",
                "Evidence examples:",
            ]
        )
        shown = 0
        seen_urls = set()
        for category in pattern["categories"]:
            for issue in examples.get(category, []):
                if issue["url"] in seen_urls:
                    continue
                seen_urls.add(issue["url"])
                shown += 1
                lines.append(
                    f"- {issue['framework']}: [{issue['issue_title']}]({issue['url']}) "
                    f"({issue['number_of_comments']} comments, state: {issue['state']})"
                )
                if shown >= 4:
                    break
            if shown >= 4:
                break
        lines.append("")
    (OUT_DOCS / "failure_patterns.md").write_text("\n".join(lines), encoding="utf-8")


def write_assumptions() -> None:
    lines = [
        "# Assumption Database",
        "",
        f"Generated on: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "| Assumption | Where It Appears | Why It Can Fail |",
        "| --- | --- | --- |",
    ]
    for assumption, where, failure in ASSUMPTIONS:
        lines.append(f"| {assumption} | {where} | {failure} |")
    (OUT_DOCS / "assumption_database.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def score_gap(pattern: dict, counts: Counter) -> dict[str, int]:
    evidence = min(10, max(1, pattern_score(pattern, counts) // 8))
    demand = min(10, max(4, pattern_score(pattern, counts) // 10))
    academic = {
        "Memory pollution and stale state": 9,
        "Tool loops and failed termination": 8,
        "Poor task decomposition": 8,
        "Wrong tool selection and schema mismatch": 9,
        "Multi-agent disagreement and deadlock": 8,
        "Context explosion": 9,
        "Recovery failure after bad actions": 7,
        "Evaluation mismatch": 9,
        "Human approval bottlenecks": 7,
        "Prompt sensitivity and hidden assumptions": 8,
    }[pattern["name"]]
    novelty = {
        "Memory pollution and stale state": 9,
        "Tool loops and failed termination": 8,
        "Poor task decomposition": 7,
        "Wrong tool selection and schema mismatch": 9,
        "Multi-agent disagreement and deadlock": 8,
        "Context explosion": 8,
        "Recovery failure after bad actions": 8,
        "Evaluation mismatch": 8,
        "Human approval bottlenecks": 7,
        "Prompt sensitivity and hidden assumptions": 8,
    }[pattern["name"]]
    architecture = {
        "Memory pollution and stale state": 9,
        "Tool loops and failed termination": 9,
        "Poor task decomposition": 8,
        "Wrong tool selection and schema mismatch": 9,
        "Multi-agent disagreement and deadlock": 9,
        "Context explosion": 8,
        "Recovery failure after bad actions": 9,
        "Evaluation mismatch": 7,
        "Human approval bottlenecks": 8,
        "Prompt sensitivity and hidden assumptions": 8,
    }[pattern["name"]]
    feasibility = {
        "Memory pollution and stale state": 8,
        "Tool loops and failed termination": 9,
        "Poor task decomposition": 8,
        "Wrong tool selection and schema mismatch": 8,
        "Multi-agent disagreement and deadlock": 7,
        "Context explosion": 8,
        "Recovery failure after bad actions": 7,
        "Evaluation mismatch": 8,
        "Human approval bottlenecks": 8,
        "Prompt sensitivity and hidden assumptions": 8,
    }[pattern["name"]]
    benchmark = 8 if "benchmark" in pattern["benchmark"].lower() else 7
    open_source = 9
    publication = 8 if novelty >= 8 and academic >= 8 else 7
    qwen = {
        "Memory pollution and stale state": 10,
        "Tool loops and failed termination": 9,
        "Poor task decomposition": 9,
        "Wrong tool selection and schema mismatch": 10,
        "Multi-agent disagreement and deadlock": 9,
        "Context explosion": 9,
        "Recovery failure after bad actions": 8,
        "Evaluation mismatch": 8,
        "Human approval bottlenecks": 8,
        "Prompt sensitivity and hidden assumptions": 8,
    }[pattern["name"]]
    return {
        "real_world_demand": demand,
        "user_evidence": evidence,
        "academic_evidence": academic,
        "novelty": novelty,
        "architecture_potential": architecture,
        "demo_feasibility": feasibility,
        "benchmark_availability": benchmark,
        "open_source_value": open_source,
        "publication_potential": publication,
        "qwen_track_fitness": qwen,
    }


def write_micro_gaps_and_ranking(counts: Counter) -> list[dict]:
    OUT_DATA.mkdir(parents=True, exist_ok=True)
    micro_rows = []
    ranking_rows = []
    variants = [
        ("policy", "What policy should decide when this mechanism activates?"),
        ("measurement", "How can this failure be measured automatically during an agent run?"),
        ("architecture", "What runtime component should own this decision instead of leaving it inside the prompt?"),
        ("adaptation", "How should the system update behavior after repeated failures?"),
    ]
    for pattern in PATTERNS:
        scores = score_gap(pattern, counts)
        total = sum(scores.values())
        ranking_rows.append(
            {
                "gap": pattern["name"],
                "research_question": pattern["question"],
                "evidence_signal": pattern_score(pattern, counts),
                **scores,
                "final_score": total,
                "possible_contribution": pattern["contribution"],
                "benchmark": pattern["benchmark"],
            }
        )
        for suffix, angle in variants:
            micro_rows.append(
                {
                    "micro_gap_id": f"{re.sub(r'[^a-z0-9]+', '-', pattern['name'].lower()).strip('-')}-{suffix}",
                    "problem_statement": pattern["name"],
                    "research_question": f"{pattern['question']} {angle}",
                    "evidence": f"{pattern_score(pattern, counts)} GitHub category hits from related issue categories.",
                    "existing_solution": pattern["current_solution"],
                    "remaining_limitation": pattern["remaining_gap"],
                    "possible_contribution": pattern["contribution"],
                    "target_benchmark": pattern["benchmark"],
                }
            )

    ranking_rows.sort(key=lambda row: row["final_score"], reverse=True)
    with (OUT_DATA / "micro_gap_database.csv").open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "micro_gap_id",
            "problem_statement",
            "research_question",
            "evidence",
            "existing_solution",
            "remaining_limitation",
            "possible_contribution",
            "target_benchmark",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(micro_rows)

    with (OUT_DATA / "gap_ranking.csv").open("w", newline="", encoding="utf-8") as file:
        fieldnames = [
            "gap",
            "research_question",
            "evidence_signal",
            "real_world_demand",
            "user_evidence",
            "academic_evidence",
            "novelty",
            "architecture_potential",
            "demo_feasibility",
            "benchmark_availability",
            "open_source_value",
            "publication_potential",
            "qwen_track_fitness",
            "final_score",
            "possible_contribution",
            "benchmark",
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ranking_rows)
    return ranking_rows


def write_analysis_summary(rows: list[dict], counts: Counter, ranking_rows: list[dict]) -> None:
    lines = [
        "# Research Analysis Summary",
        "",
        f"Generated on: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Evidence Base",
        "",
        f"- GitHub issues collected: {len(rows)}",
        f"- Repositories analyzed: {len(TARGET_REPOS)}",
        "- Reddit, Hacker News, and papers are not yet included in this run.",
        "",
        "## Pain Point Distribution",
        "",
        "| Category | Issue Hits |",
        "| --- | ---: |",
    ]
    for category, count in counts.most_common():
        lines.append(f"| {category} | {count} |")

    lines.extend(["", "## Top Ranked Research Gaps", "", "| Rank | Gap | Score | Research Question |", "| --- | --- | ---: | --- |"])
    for index, row in enumerate(ranking_rows[:10], start=1):
        lines.append(f"| {index} | {row['gap']} | {row['final_score']} | {row['research_question']} |")

    lines.extend(
        [
            "",
            "## Shortlist Recommendation For Review",
            "",
            "These are not final hackathon ideas yet. They are the strongest evidence-backed micro-gap families to review before Milestone B:",
        ]
    )
    for row in ranking_rows[:5]:
        lines.append(f"- {row['gap']}: {row['research_question']}")

    lines.extend(
        [
            "",
            "## Next Research Steps",
            "",
            "- Add Reddit and Hacker News discussions for non-repository user pain.",
            "- Add 40-60 recent papers to validate academic support.",
            "- Manually inspect the top 30 GitHub issues by comments/reactions for richer qualitative evidence.",
            "- After choosing 3-5 micro-gaps, proceed to Milestone B ideation and architecture design.",
        ]
    )
    (OUT_DOCS / "research_analysis.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = collect_issues()
    write_issues(rows)
    counts, examples = evidence_counts(rows)
    write_failure_patterns(rows, counts, examples)
    write_assumptions()
    ranking_rows = write_micro_gaps_and_ranking(counts)
    write_analysis_summary(rows, counts, ranking_rows)
    print(f"Wrote {OUT_DATA / 'issues_database.csv'}")
    print(f"Wrote {OUT_DOCS / 'failure_patterns.md'}")
    print(f"Wrote {OUT_DOCS / 'assumption_database.md'}")
    print(f"Wrote {OUT_DATA / 'micro_gap_database.csv'}")
    print(f"Wrote {OUT_DATA / 'gap_ranking.csv'}")
    print(f"Wrote {OUT_DOCS / 'research_analysis.md'}")


if __name__ == "__main__":
    main()
