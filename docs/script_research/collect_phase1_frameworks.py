#!/usr/bin/env python3
"""Collect Phase 1 AI agent framework landscape data.

The script combines curated research fields with live GitHub repository
metadata. It writes the required Phase 1 deliverables:

- data/phase1/framework_database.csv
- docs/phase1/framework_summary.md
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "phase1"
DOC_DIR = ROOT / "docs" / "phase1"
USER_AGENT = "qwen-practice-phase1-research"


FRAMEWORKS = [
    {
        "name": "LangGraph",
        "repo": "langchain-ai/langgraph",
        "category": "Agent orchestration framework",
        "main_architecture": "Stateful graph runtime with nodes, edges, reducers, checkpointing, durable execution, streaming, and human-in-the-loop control.",
        "supported_features": "Graph workflows; persistence; memory/checkpointing; tool use; streaming; interrupts; subgraphs; multi-agent patterns; LangSmith observability.",
        "core_assumptions": "Agent behavior can be made reliable by explicit state transitions and recoverable graph execution.",
        "strengths": "Strong control over long-running workflows; production-oriented durability; flexible graph composition.",
        "weaknesses": "Requires developers to model state and transitions explicitly; learning curve is higher than prompt-first frameworks.",
        "known_limitations": "Reliability depends on graph design, state schema, and external tool correctness; evaluation is usually delegated to LangSmith or custom harnesses.",
        "relevant_papers_blogs": "https://docs.langchain.com/oss/python/langgraph/overview | https://www.langchain.com/langgraph",
    },
    {
        "name": "Microsoft AutoGen",
        "repo": "microsoft/autogen",
        "category": "Multi-agent framework",
        "main_architecture": "Actor-style multi-agent programming framework with agents, messages, teams, tools, and event-driven runtimes.",
        "supported_features": "Multi-agent conversations; tool calling; human involvement; distributed runtimes; model clients; agent teams.",
        "core_assumptions": "Complex tasks can be decomposed into interacting specialist agents with explicit message protocols.",
        "strengths": "Influential research lineage; strong multi-agent abstractions; broad examples and academic visibility.",
        "weaknesses": "Version transitions created migration friction; older AutoGen APIs are in maintenance mode.",
        "known_limitations": "Coordination quality remains sensitive to prompts, team topology, and termination conditions.",
        "relevant_papers_blogs": "https://microsoft.github.io/autogen/stable/ | https://github.com/microsoft/autogen | https://arxiv.org/abs/2308.08155",
    },
    {
        "name": "CrewAI",
        "repo": "crewAIInc/crewAI",
        "category": "Multi-agent orchestration framework",
        "main_architecture": "Role-based crews of agents executing tasks through sequential, hierarchical, or flow-style processes.",
        "supported_features": "Roles; goals; tasks; tools; process orchestration; flows; knowledge; memory; observability integrations.",
        "core_assumptions": "Human-like role assignment and task delegation can improve agent collaboration and developer usability.",
        "strengths": "Approachable mental model; fast prototyping; strong community adoption.",
        "weaknesses": "Abstractions can hide execution details; role prompts may become brittle as workflows grow.",
        "known_limitations": "Difficult to guarantee correctness or convergence in open-ended crews without external evaluation gates.",
        "relevant_papers_blogs": "https://docs.crewai.com/ | https://github.com/crewAIInc/crewAI",
    },
    {
        "name": "Letta",
        "repo": "letta-ai/letta",
        "category": "Agent memory system",
        "main_architecture": "Stateful agent server with memory blocks, archival memory, tools, data sources, and persistent agent state.",
        "supported_features": "Long-term memory; tool calling; agent server; ADE UI; data sources; model-provider abstraction; multi-agent examples.",
        "core_assumptions": "Persistent memory should be an explicit first-class part of the agent runtime.",
        "strengths": "Memory-centric architecture; strong research roots from MemGPT; clear focus on stateful agents.",
        "weaknesses": "Operational complexity is higher than stateless SDKs; memory quality depends on write/retrieval policies.",
        "known_limitations": "Memory pollution, stale facts, and retrieval relevance remain open design problems.",
        "relevant_papers_blogs": "https://docs.letta.com/ | https://github.com/letta-ai/letta | https://arxiv.org/abs/2310.08560",
    },
    {
        "name": "Mem0",
        "repo": "mem0ai/mem0",
        "category": "Agent memory system",
        "main_architecture": "Memory layer/API that extracts, stores, updates, and retrieves user and agent memories across applications.",
        "supported_features": "User memory; agent memory; vector and graph memory; hosted API; open-source SDK; multi-provider storage.",
        "core_assumptions": "A reusable memory layer can improve personalization and continuity across agent sessions.",
        "strengths": "Narrow, practical memory focus; easy to embed into existing agent stacks.",
        "weaknesses": "Less of a full orchestration framework; downstream agent behavior still needs separate control logic.",
        "known_limitations": "Deciding what deserves memory, when to update it, and how to resolve conflicts is still application-specific.",
        "relevant_papers_blogs": "https://docs.mem0.ai/ | https://github.com/mem0ai/mem0",
    },
    {
        "name": "OpenHands",
        "repo": "All-Hands-AI/OpenHands",
        "category": "Software engineering agent",
        "main_architecture": "Autonomous coding agent runtime with browser, shell, editor, sandbox, event stream, and task execution loop.",
        "supported_features": "Code editing; terminal use; browsing; issue solving; sandboxing; trajectories; evaluations; GitHub integration.",
        "core_assumptions": "Software tasks can be solved by agents operating in a realistic developer environment with tools and feedback.",
        "strengths": "Strong benchmark orientation; realistic tool environment; active open-source community.",
        "weaknesses": "High compute/cost for long tasks; failures can come from planning, environment handling, or tool misuse.",
        "known_limitations": "Long-horizon reliability, repository understanding, and recovery from bad edits remain hard.",
        "relevant_papers_blogs": "https://github.com/All-Hands-AI/OpenHands | https://docs.all-hands.dev/",
    },
    {
        "name": "Browser Use",
        "repo": "browser-use/browser-use",
        "category": "Browser automation agent framework",
        "main_architecture": "LLM-driven browser control layer using Playwright-style browser state, actions, and task loops.",
        "supported_features": "Browser navigation; DOM/action extraction; multi-step web tasks; tool calling; model-provider support; cloud option.",
        "core_assumptions": "Web task automation improves when the agent receives structured browser state and controlled actions.",
        "strengths": "Focused browser automation; useful for real web workflows; simple developer entry point.",
        "weaknesses": "Highly dependent on website stability, auth flows, and model visual/DOM reasoning.",
        "known_limitations": "CAPTCHAs, dynamic UIs, ambiguous pages, and long web tasks can break reliability.",
        "relevant_papers_blogs": "https://docs.browser-use.com/ | https://github.com/browser-use/browser-use",
    },
    {
        "name": "SmolAgents",
        "repo": "huggingface/smolagents",
        "category": "Tool-use agent framework",
        "main_architecture": "Minimal agent framework with code agents, tool abstractions, managed agents, and Hugging Face ecosystem integration.",
        "supported_features": "Code execution agents; tool calling; managed agents; local/hosted models; Hugging Face Hub tools.",
        "core_assumptions": "Small composable abstractions plus executable code actions are enough for many agent workflows.",
        "strengths": "Lightweight; readable; integrates naturally with open models and Hugging Face tooling.",
        "weaknesses": "Less built-in production orchestration than heavier graph/runtime frameworks.",
        "known_limitations": "Sandboxing, evaluation, persistence, and complex workflow control need additional engineering.",
        "relevant_papers_blogs": "https://huggingface.co/docs/smolagents | https://github.com/huggingface/smolagents",
    },
    {
        "name": "OpenAI Agents SDK",
        "repo": "openai/openai-agents-python",
        "category": "Agent SDK",
        "main_architecture": "Lightweight SDK with agents, tools, handoffs, guardrails, sessions, tracing, and model-provider abstractions.",
        "supported_features": "Tool calling; multi-agent handoffs; guardrails; tracing; sessions; structured outputs; MCP integration.",
        "core_assumptions": "Most production agent apps need a small set of primitives rather than a large framework.",
        "strengths": "Simple API; first-party tracing; production orientation; good fit for OpenAI Responses and tool ecosystems.",
        "weaknesses": "Less opinionated workflow planning than graph frameworks; deep customization may require application code.",
        "known_limitations": "Correctness still depends on prompts, tool schemas, guardrail quality, and app-owned state management.",
        "relevant_papers_blogs": "https://openai.github.io/openai-agents-python/ | https://developers.openai.com/api/docs/guides/agents | https://github.com/openai/openai-agents-python",
    },
    {
        "name": "Claude Code",
        "repo": "anthropics/claude-code-action",
        "category": "Software engineering agent",
        "main_architecture": "Agentic coding product and GitHub Action built around repository context, tool execution, and review/change workflows.",
        "supported_features": "Code generation; repository edits; GitHub issue/PR workflows; code review; terminal-style task execution in product surfaces.",
        "core_assumptions": "Coding agents become useful when embedded directly into developer workflows and repository context.",
        "strengths": "Strong developer workflow focus; practical coding UX; GitHub automation entry point.",
        "weaknesses": "Core product is not a general open-source framework; less transparent internals for research replication.",
        "known_limitations": "Research reuse is constrained by closed product behavior; public GitHub stars reflect the action, not the full product.",
        "relevant_papers_blogs": "https://docs.anthropic.com/en/docs/claude-code | https://github.com/anthropics/claude-code-action",
    },
    {
        "name": "LlamaIndex Agents",
        "repo": "run-llama/llama_index",
        "category": "RAG and agent framework",
        "main_architecture": "Data framework with indexes, query engines, tools, workflows, and agent abstractions over private/structured data.",
        "supported_features": "RAG; tools; workflows; agents; data connectors; evaluators; observability integrations; structured extraction.",
        "core_assumptions": "Agents need high-quality data interfaces and retrieval abstractions as much as reasoning loops.",
        "strengths": "Excellent data connector/index ecosystem; strong RAG foundations; broad production examples.",
        "weaknesses": "Large surface area; agent behavior may be secondary to data framework complexity.",
        "known_limitations": "Retrieval quality, grounding, and evaluation remain application-dependent.",
        "relevant_papers_blogs": "https://docs.llamaindex.ai/ | https://github.com/run-llama/llama_index",
    },
    {
        "name": "Haystack Agents",
        "repo": "deepset-ai/haystack",
        "category": "RAG and agent framework",
        "main_architecture": "Pipeline/component framework for retrieval, generation, tools, routers, evaluators, and agentic RAG systems.",
        "supported_features": "Pipelines; RAG; tool calling; document stores; evaluation; tracing integrations; production components.",
        "core_assumptions": "Composable NLP/RAG components can be assembled into reliable agentic applications.",
        "strengths": "Mature search/RAG engineering; pipeline clarity; enterprise-friendly architecture.",
        "weaknesses": "Agent-specific abstractions are less central than pipelines and RAG components.",
        "known_limitations": "Complex agent planning and memory usually require custom components or external orchestration.",
        "relevant_papers_blogs": "https://docs.haystack.deepset.ai/ | https://github.com/deepset-ai/haystack",
    },
    {
        "name": "Flowise",
        "repo": "FlowiseAI/Flowise",
        "category": "Low-code agent builder",
        "main_architecture": "Visual low-code builder for LLM flows, chatflows, agents, tools, vector stores, and deployment endpoints.",
        "supported_features": "Drag-and-drop workflows; agents; RAG; tools; templates; API deployment; integrations.",
        "core_assumptions": "Visual composition lowers the barrier for building agentic workflows.",
        "strengths": "Fast prototyping; accessible UI; broad integration catalog.",
        "weaknesses": "Complex flows can become hard to reason about, version, and test.",
        "known_limitations": "Research contribution is limited unless paired with new execution/evaluation mechanisms.",
        "relevant_papers_blogs": "https://docs.flowiseai.com/ | https://github.com/FlowiseAI/Flowise",
    },
    {
        "name": "Dify",
        "repo": "langgenius/dify",
        "category": "LLM application platform",
        "main_architecture": "Open-source platform for workflows, agents, RAG, model routing, prompt management, datasets, and operations.",
        "supported_features": "Agent apps; workflow builder; RAG; tools; model management; monitoring; evaluation datasets; app publishing.",
        "core_assumptions": "Teams need an integrated platform to operationalize LLM applications and agents.",
        "strengths": "Full-stack product surface; strong adoption; useful app lifecycle features.",
        "weaknesses": "Platform breadth can obscure low-level agent control; research novelty often lives outside the platform.",
        "known_limitations": "Agent reliability still depends on workflow design, tools, retrieval, and model behavior.",
        "relevant_papers_blogs": "https://docs.dify.ai/ | https://github.com/langgenius/dify",
    },
    {
        "name": "Agno",
        "repo": "agno-agi/agno",
        "category": "Agent framework",
        "main_architecture": "Python framework for agents, teams, tools, memory, knowledge, reasoning, and multimodal workflows.",
        "supported_features": "Agents; teams; memory; knowledge bases; tools; reasoning; multimodal models; monitoring.",
        "core_assumptions": "Developers benefit from a compact framework that bundles agent primitives with memory and knowledge.",
        "strengths": "Pragmatic API; broad feature coverage; good examples for agent teams.",
        "weaknesses": "Broad abstractions may overlap with other frameworks; deeper guarantees are limited.",
        "known_limitations": "Coordination, evaluation, and long-running state correctness need external validation.",
        "relevant_papers_blogs": "https://docs.agno.com/ | https://github.com/agno-agi/agno",
    },
    {
        "name": "CAMEL-AI",
        "repo": "camel-ai/camel",
        "category": "Multi-agent research framework",
        "main_architecture": "Research-oriented society-of-agents framework with role-playing agents, toolkits, memory, data generation, and benchmarks.",
        "supported_features": "Multi-agent role play; tools; memory; datasets; workforce patterns; model support; simulation examples.",
        "core_assumptions": "Role-playing and communicative agents can simulate cooperative problem solving and generate useful data.",
        "strengths": "Strong academic identity; broad multi-agent experiments; useful for simulation and research prototypes.",
        "weaknesses": "Research abstractions may require hardening for production use.",
        "known_limitations": "Role-play conversations can drift; evaluation of emergent collaboration is difficult.",
        "relevant_papers_blogs": "https://docs.camel-ai.org/ | https://github.com/camel-ai/camel | https://arxiv.org/abs/2303.17760",
    },
    {
        "name": "Qwen-Agent",
        "repo": "QwenLM/Qwen-Agent",
        "category": "Qwen-native agent framework",
        "main_architecture": "Framework for Qwen-based LLM applications with agents, tools, planning, memory, browser assistant, and code interpreter examples.",
        "supported_features": "Qwen model support; tool use; planning; memory; function calling; browser assistant; code interpreter; custom assistants.",
        "core_assumptions": "Qwen instruction following, tool use, planning, and memory can form a practical native agent stack.",
        "strengths": "Direct Qwen ecosystem fit; useful examples; relevant to the hackathon track.",
        "weaknesses": "Smaller ecosystem than larger cross-provider frameworks.",
        "known_limitations": "Less third-party evaluation and fewer production case studies than older frameworks.",
        "relevant_papers_blogs": "https://qwenlm.github.io/Qwen-Agent/en/ | https://github.com/QwenLM/Qwen-Agent",
    },
    {
        "name": "AutoGPT",
        "repo": "Significant-Gravitas/AutoGPT",
        "category": "Autonomous agent platform",
        "main_architecture": "Agent platform/server and historical autonomous task loop with tools, marketplace-style blocks, and workflow automation.",
        "supported_features": "Autonomous task execution; workflows; tools/blocks; marketplace; frontend/server; benchmarks in earlier ecosystem.",
        "core_assumptions": "Goal-directed agents can iteratively plan, act, observe, and refine toward broad user objectives.",
        "strengths": "Very high mindshare; early autonomous-agent catalyst; large community.",
        "weaknesses": "Historical fully autonomous loops were brittle and costly; project scope has shifted over time.",
        "known_limitations": "Open-ended autonomy remains vulnerable to loops, hallucinated plans, and tool misuse.",
        "relevant_papers_blogs": "https://github.com/Significant-Gravitas/AutoGPT | https://docs.agpt.co/",
    },
    {
        "name": "Semantic Kernel",
        "repo": "microsoft/semantic-kernel",
        "category": "Agent and orchestration SDK",
        "main_architecture": "SDK for AI orchestration with plugins, planners, functions, memories/connectors, and agent abstractions across .NET/Python/Java.",
        "supported_features": "Plugins; function calling; planners; agents; memory connectors; process framework; Microsoft ecosystem integration.",
        "core_assumptions": "Enterprise applications need typed orchestration and plugin/function abstractions around LLMs.",
        "strengths": "Enterprise-friendly; multi-language; strong Microsoft ecosystem alignment.",
        "weaknesses": "Can feel heavier than minimal SDKs; agent APIs evolve with platform direction.",
        "known_limitations": "Planning quality and agent reliability still require careful constraints and evaluation.",
        "relevant_papers_blogs": "https://learn.microsoft.com/semantic-kernel/ | https://github.com/microsoft/semantic-kernel",
    },
    {
        "name": "Google Agent Development Kit",
        "repo": "google/adk-python",
        "category": "Agent SDK",
        "main_architecture": "Code-first agent framework with agents, tools, sessions, memory, callbacks, evaluation, deployment, and Google ecosystem integrations.",
        "supported_features": "Multi-agent systems; tool use; sessions; memory; evaluation; tracing; deployment; Gemini/Vertex integrations.",
        "core_assumptions": "Production agents need a code-first SDK plus evaluation and deployment hooks.",
        "strengths": "Strong evaluation/deployment story; natural fit for Gemini and Google Cloud.",
        "weaknesses": "Younger ecosystem than LangChain/LlamaIndex; strongest path is Google-centric.",
        "known_limitations": "Cross-provider portability and independent community examples are still maturing.",
        "relevant_papers_blogs": "https://google.github.io/adk-docs/ | https://github.com/google/adk-python",
    },
    {
        "name": "Microsoft Agent Framework",
        "repo": "microsoft/agent-framework",
        "category": "Agent orchestration framework",
        "main_architecture": "Production-grade framework combining AutoGen-style multi-agent orchestration with Semantic Kernel-style enterprise capabilities.",
        "supported_features": "Agents; workflows; multi-language support; multi-agent orchestration; enterprise connectors; .NET and Python.",
        "core_assumptions": "Enterprise agent systems need unified orchestration, extensibility, and integration patterns.",
        "strengths": "Clear successor direction for Microsoft agent tooling; enterprise positioning; multi-language target.",
        "weaknesses": "Newer project with less historical community evidence.",
        "known_limitations": "Ecosystem maturity and migration path from older Microsoft agent tools are still developing.",
        "relevant_papers_blogs": "https://github.com/microsoft/agent-framework | https://learn.microsoft.com/agent-framework/",
    },
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
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data, response.headers
    except urllib.error.HTTPError as exc:
        print(f"GitHub API error {exc.code} for {path}", file=sys.stderr)
    except Exception as exc:
        print(f"GitHub API error for {path}: {exc}", file=sys.stderr)
    return None, {}


def contributor_count(repo: str) -> str:
    encoded = urllib.parse.quote(repo, safe="/")
    _data, headers = github_get(f"/repos/{encoded}/contributors?per_page=1&anon=1")
    link = headers.get("Link", "")
    if 'rel="last"' in link:
        for part in link.split(","):
            if 'rel="last"' in part:
                url = part.split(";")[0].strip(" <>")
                query = urllib.parse.urlparse(url).query
                params = urllib.parse.parse_qs(query)
                return params.get("page", [""])[0]
    data, _headers = github_get(f"/repos/{encoded}/contributors?per_page=100&anon=1")
    if isinstance(data, list):
        return str(len(data))
    return ""


def latest_release(repo: str) -> tuple[str, str]:
    encoded = urllib.parse.quote(repo, safe="/")
    data, _headers = github_get(f"/repos/{encoded}/releases/latest")
    if isinstance(data, dict):
        return data.get("tag_name", ""), data.get("published_at", "")
    return "", ""


def maintenance_status(pushed_at: str, archived: bool, disabled: bool) -> str:
    if archived or disabled:
        return "inactive/archived"
    if not pushed_at:
        return "unknown"
    pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    age_days = (datetime.now(timezone.utc) - pushed).days
    if age_days <= 30:
        return "active: pushed within 30 days"
    if age_days <= 90:
        return "active: pushed within 90 days"
    if age_days <= 180:
        return "moderate: pushed within 180 days"
    return "low: no push in 180+ days"


def enrich(row: dict) -> dict:
    repo = row["repo"]
    encoded = urllib.parse.quote(repo, safe="/")
    data, _headers = github_get(f"/repos/{encoded}")
    time.sleep(0.15)

    enriched = dict(row)
    enriched.update(
        {
            "github_url": f"https://github.com/{repo}",
            "repo_created_at": "",
            "release_date": "",
            "latest_release": "",
            "latest_release_date": "",
            "github_stars": "",
            "forks": "",
            "open_issues": "",
            "watchers": "",
            "contributors_estimate": "",
            "community_size": "",
            "last_push": "",
            "active_maintenance": "unknown",
            "license": "",
        }
    )

    if isinstance(data, dict) and "full_name" in data:
        latest_tag, latest_date = latest_release(repo)
        time.sleep(0.15)
        contributors = contributor_count(repo)
        stars = data.get("stargazers_count", "")
        forks = data.get("forks_count", "")
        watchers = data.get("subscribers_count", "")
        community_parts = []
        if stars != "":
            community_parts.append(f"{stars} stars")
        if forks != "":
            community_parts.append(f"{forks} forks")
        if contributors:
            community_parts.append(f"{contributors} contributors")
        enriched.update(
            {
                "repo_created_at": data.get("created_at", ""),
                "release_date": data.get("created_at", ""),
                "latest_release": latest_tag,
                "latest_release_date": latest_date,
                "github_stars": stars,
                "forks": forks,
                "open_issues": data.get("open_issues_count", ""),
                "watchers": watchers,
                "contributors_estimate": contributors,
                "community_size": "; ".join(community_parts),
                "last_push": data.get("pushed_at", ""),
                "active_maintenance": maintenance_status(
                    data.get("pushed_at", ""),
                    bool(data.get("archived")),
                    bool(data.get("disabled")),
                ),
                "license": (data.get("license") or {}).get("spdx_id", ""),
            }
        )
    return enriched


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "framework_database.csv"
    fieldnames = [
        "name",
        "category",
        "release_date",
        "repo_created_at",
        "main_architecture",
        "supported_features",
        "core_assumptions",
        "strengths",
        "weaknesses",
        "known_limitations",
        "github_stars",
        "community_size",
        "active_maintenance",
        "last_push",
        "latest_release",
        "latest_release_date",
        "forks",
        "watchers",
        "contributors_estimate",
        "open_issues",
        "license",
        "github_url",
        "relevant_papers_blogs",
    ]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_summary(rows: list[dict]) -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    path = DOC_DIR / "framework_summary.md"
    sorted_by_stars = sorted(
        rows,
        key=lambda item: int(item["github_stars"] or 0),
        reverse=True,
    )
    categories = {}
    for row in rows:
        categories[row["category"]] = categories.get(row["category"], 0) + 1

    lines = [
        "# Phase 1 - AI Agent Ecosystem Survey",
        "",
        f"Generated on: {datetime.now(timezone.utc).date().isoformat()}",
        "",
        "## Scope",
        "",
        f"This initial pass surveys {len(rows)} frameworks across agent orchestration, multi-agent systems, memory systems, tool-use frameworks, browser/coding agents, RAG-agent stacks, low-code platforms, and evaluation-oriented SDKs.",
        "",
        "## Category Coverage",
        "",
    ]
    for category, count in sorted(categories.items()):
        lines.append(f"- {category}: {count}")

    lines.extend(
        [
            "",
            "## Highest GitHub Adoption",
            "",
            "| Rank | Framework | Stars | Maintenance | Category |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for index, row in enumerate(sorted_by_stars[:10], start=1):
        lines.append(
            f"| {index} | [{row['name']}]({row['github_url']}) | {row['github_stars']} | {row['active_maintenance']} | {row['category']} |"
        )

    lines.extend(
        [
            "",
            "## Ecosystem Observations",
            "",
            "- The ecosystem is splitting into several layers: low-level orchestration runtimes, memory subsystems, developer/coding agents, browser agents, RAG-agent data frameworks, and low-code operational platforms.",
            "- Graph and workflow runtimes such as LangGraph, Microsoft Agent Framework, Google ADK, and Semantic Kernel emphasize explicit state, tool control, and production execution.",
            "- Multi-agent frameworks such as AutoGen, CrewAI, CAMEL-AI, and Agno make collaboration easier to express, but still leave coordination correctness and convergence mostly to prompts, topology, and custom stop conditions.",
            "- Memory-first systems such as Letta and Mem0 make persistence explicit, but memory write policy, conflict resolution, stale facts, and retrieval relevance remain unresolved research surfaces.",
            "- Coding and browser agents expose the hardest real-world setting: long-horizon action, changing environments, partial observability, recovery from mistakes, and tool-side side effects.",
            "- Low-code platforms such as Flowise and Dify are excellent for adoption, but their research value depends on whether they introduce a new mechanism rather than merely wrapping existing components.",
            "",
            "## Recurring Limitations",
            "",
            "- Planning reliability degrades on long-horizon tasks.",
            "- Tool selection and tool-loop termination are still fragile.",
            "- Memory systems struggle with what to store, what to forget, and how to resolve contradictions.",
            "- Multi-agent systems lack strong guarantees around disagreement, deadlock, redundant work, and accountability.",
            "- Evaluation is fragmented: most frameworks provide hooks, traces, or examples, but objective task-level benchmarks must often be added separately.",
            "- Production readiness depends heavily on application-specific guardrails, permissions, observability, and rollback behavior.",
            "",
            "## Qwen Hackathon Relevance",
            "",
            "Qwen-Agent is the most direct ecosystem fit, while LangGraph, AutoGen, CrewAI, Letta, Mem0, OpenHands, Browser Use, and CAMEL-AI provide strong comparison baselines for agent architecture, memory, tool use, and multi-agent behavior. For later phases, the most promising evidence targets are memory policy, long-horizon recovery, tool-use reliability, multi-agent coordination, and evaluation mismatch.",
            "",
            "## Notes",
            "",
            "- `release_date` uses the public GitHub repository creation date as the initial public release proxy when a canonical first release is not available.",
            "- Community size is approximated from public stars, forks, and contributor counts.",
            "- GitHub data is a snapshot and should be regenerated before final reporting.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = []
    for framework in FRAMEWORKS:
        print(f"Collecting {framework['name']}...", file=sys.stderr)
        rows.append(enrich(framework))
        time.sleep(0.15)
    write_csv(rows)
    write_summary(rows)
    print(f"Wrote {OUT_DIR / 'framework_database.csv'}")
    print(f"Wrote {DOC_DIR / 'framework_summary.md'}")


if __name__ == "__main__":
    main()
