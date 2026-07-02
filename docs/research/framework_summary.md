# Phase 1 - AI Agent Ecosystem Survey

Generated on: 2026-06-30

## Scope

This initial pass surveys 21 frameworks across agent orchestration, multi-agent systems, memory systems, tool-use frameworks, browser/coding agents, RAG-agent stacks, low-code platforms, and evaluation-oriented SDKs.

## Category Coverage

- Agent SDK: 2
- Agent and orchestration SDK: 1
- Agent framework: 1
- Agent memory system: 2
- Agent orchestration framework: 2
- Autonomous agent platform: 1
- Browser automation agent framework: 1
- LLM application platform: 1
- Low-code agent builder: 1
- Multi-agent framework: 1
- Multi-agent orchestration framework: 1
- Multi-agent research framework: 1
- Qwen-native agent framework: 1
- RAG and agent framework: 2
- Software engineering agent: 2
- Tool-use agent framework: 1

## Highest GitHub Adoption

| Rank | Framework | Stars | Maintenance | Category |
| --- | --- | ---: | --- | --- |
| 1 | [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) | 185225 | active: pushed within 30 days | Autonomous agent platform |
| 2 | [Dify](https://github.com/langgenius/dify) | 147094 | active: pushed within 30 days | LLM application platform |
| 3 | [Browser Use](https://github.com/browser-use/browser-use) | 101568 | active: pushed within 30 days | Browser automation agent framework |
| 4 | [OpenHands](https://github.com/All-Hands-AI/OpenHands) | 78777 | active: pushed within 30 days | Software engineering agent |
| 5 | [Mem0](https://github.com/mem0ai/mem0) | 59755 | active: pushed within 30 days | Agent memory system |
| 6 | [Microsoft AutoGen](https://github.com/microsoft/autogen) | 59373 | active: pushed within 90 days | Multi-agent framework |
| 7 | [CrewAI](https://github.com/crewAIInc/crewAI) | 54612 | active: pushed within 30 days | Multi-agent orchestration framework |
| 8 | [Flowise](https://github.com/FlowiseAI/Flowise) | 54131 | active: pushed within 30 days | Low-code agent builder |
| 9 | [LlamaIndex Agents](https://github.com/run-llama/llama_index) | 50531 | active: pushed within 30 days | RAG and agent framework |
| 10 | [Agno](https://github.com/agno-agi/agno) | 40914 | active: pushed within 30 days | Agent framework |

## Ecosystem Observations

- The ecosystem is splitting into several layers: low-level orchestration runtimes, memory subsystems, developer/coding agents, browser agents, RAG-agent data frameworks, and low-code operational platforms.
- Graph and workflow runtimes such as LangGraph, Microsoft Agent Framework, Google ADK, and Semantic Kernel emphasize explicit state, tool control, and production execution.
- Multi-agent frameworks such as AutoGen, CrewAI, CAMEL-AI, and Agno make collaboration easier to express, but still leave coordination correctness and convergence mostly to prompts, topology, and custom stop conditions.
- Memory-first systems such as Letta and Mem0 make persistence explicit, but memory write policy, conflict resolution, stale facts, and retrieval relevance remain unresolved research surfaces.
- Coding and browser agents expose the hardest real-world setting: long-horizon action, changing environments, partial observability, recovery from mistakes, and tool-side side effects.
- Low-code platforms such as Flowise and Dify are excellent for adoption, but their research value depends on whether they introduce a new mechanism rather than merely wrapping existing components.

## Recurring Limitations

- Planning reliability degrades on long-horizon tasks.
- Tool selection and tool-loop termination are still fragile.
- Memory systems struggle with what to store, what to forget, and how to resolve contradictions.
- Multi-agent systems lack strong guarantees around disagreement, deadlock, redundant work, and accountability.
- Evaluation is fragmented: most frameworks provide hooks, traces, or examples, but objective task-level benchmarks must often be added separately.
- Production readiness depends heavily on application-specific guardrails, permissions, observability, and rollback behavior.

## Qwen Hackathon Relevance

Qwen-Agent is the most direct ecosystem fit, while LangGraph, AutoGen, CrewAI, Letta, Mem0, OpenHands, Browser Use, and CAMEL-AI provide strong comparison baselines for agent architecture, memory, tool use, and multi-agent behavior. For later phases, the most promising evidence targets are memory policy, long-horizon recovery, tool-use reliability, multi-agent coordination, and evaluation mismatch.

## Notes

- `release_date` uses the public GitHub repository creation date as the initial public release proxy when a canonical first release is not available.
- Community size is approximated from public stars, forks, and contributor counts.
- GitHub data is a snapshot and should be regenerated before final reporting.
