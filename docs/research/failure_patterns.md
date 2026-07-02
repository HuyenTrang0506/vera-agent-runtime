# Failure Patterns

Generated on: 2026-06-30

Evidence base: 766 recent GitHub issues across 12 agent repositories.

## Recovery failure after bad actions

Problem: Agents often retry without identifying the smallest recoverable state boundary.

Frequency signal: 1216 category hits across Long-term tasks, Reliability, Workflow, Tool Calling.

Current solution: Retries, checkpoints, human approval, and manual rollback.

Remaining gap: Agents often retry without identifying the smallest recoverable state boundary.

Evidence examples:
- LangGraph: [Docs safety guidance: auditable final-state receipts for agent completion claims?](https://github.com/langchain-ai/langgraph/issues/7844) (22 comments, state: open)
- LangGraph: [Collaboration: Trust-gated checkpoints and governance nodes for LangGraph](https://github.com/langchain-ai/langgraph/issues/7303) (22 comments, state: open)
- OpenAI Agents SDK: [Retry mechanism for ModelBehaviorError](https://github.com/openai/openai-agents-python/issues/325) (15 comments, state: open)
- LangGraph: [[Feature Request]: Add a high-level ApprovalNode for Human-in-the-Loop workflows](https://github.com/langchain-ai/langgraph/issues/8026) (18 comments, state: open)

## Tool loops and failed termination

Problem: Most systems stop loops mechanically rather than diagnosing why the same action keeps recurring.

Frequency signal: 1066 category hits across Tool Calling, Planning, Reliability, Cost.

Current solution: Max-iteration caps, stop conditions, retries, traces, and guardrails.

Remaining gap: Most systems stop loops mechanically rather than diagnosing why the same action keeps recurring.

Evidence examples:
- LangGraph: [🚧 LangGraph v1 roadmap – feedback wanted!](https://github.com/langchain-ai/langgraph/issues/4973) (82 comments, state: open)
- CrewAI: [[FEATURE] GuardrailProvider interface for pre-tool-call authorization](https://github.com/crewAIInc/crewAI/issues/4877) (105 comments, state: open)
- Microsoft AutoGen: [Multi-agent systems need a 'mission keeper' role — not a Boss Agent, but a dedicated goal integrity node](https://github.com/microsoft/autogen/issues/7487) (71 comments, state: open)
- CrewAI: [Tool re-execution on task retry has no idempotency guard — duplicate payments, emails, trades possible](https://github.com/crewAIInc/crewAI/issues/5802) (67 comments, state: open)

## Wrong tool selection and schema mismatch

Problem: Agents often choose plausible tools without causal evidence that the tool can change the task state.

Frequency signal: 929 category hits across Tool Calling, Hallucination, Reliability.

Current solution: Better tool descriptions, JSON schema validation, retries, and model-native function calling.

Remaining gap: Agents often choose plausible tools without causal evidence that the tool can change the task state.

Evidence examples:
- LangGraph: [🚧 LangGraph v1 roadmap – feedback wanted!](https://github.com/langchain-ai/langgraph/issues/4973) (82 comments, state: open)
- CrewAI: [[FEATURE] GuardrailProvider interface for pre-tool-call authorization](https://github.com/crewAIInc/crewAI/issues/4877) (105 comments, state: open)
- Microsoft AutoGen: [Multi-agent systems need a 'mission keeper' role — not a Boss Agent, but a dedicated goal integrity node](https://github.com/microsoft/autogen/issues/7487) (71 comments, state: open)
- CrewAI: [Tool re-execution on task retry has no idempotency guard — duplicate payments, emails, trades possible](https://github.com/crewAIInc/crewAI/issues/5802) (67 comments, state: open)

## Poor task decomposition

Problem: Decomposition quality is rarely evaluated before execution, so weak plans consume tools and context.

Frequency signal: 727 category hits across Planning, Workflow, Reliability.

Current solution: Planner prompts, graph nodes, task lists, and hierarchical managers.

Remaining gap: Decomposition quality is rarely evaluated before execution, so weak plans consume tools and context.

Evidence examples:
- LangGraph: [🚧 LangGraph v1 roadmap – feedback wanted!](https://github.com/langchain-ai/langgraph/issues/4973) (82 comments, state: open)
- Microsoft AutoGen: [Multi-agent systems need a 'mission keeper' role — not a Boss Agent, but a dedicated goal integrity node](https://github.com/microsoft/autogen/issues/7487) (71 comments, state: open)
- Microsoft AutoGen: [[Question] Practical reliability patterns for multi-agent production](https://github.com/microsoft/autogen/issues/7265) (41 comments, state: open)
- Dify: [After deploying dify 1.15.0, the frontend throws errors, please refer to the screenshot.](https://github.com/langgenius/dify/issues/38107) (16 comments, state: open)

## Evaluation mismatch

Problem: Framework-level metrics often measure execution traces but not whether user intent was satisfied robustly.

Frequency signal: 706 category hits across Evaluation, Reliability, Workflow.

Current solution: Traces, unit tests, benchmark tasks, human review, and LLM-as-judge.

Remaining gap: Framework-level metrics often measure execution traces but not whether user intent was satisfied robustly.

Evidence examples:
- Microsoft AutoGen: [Feature: Cryptographic action receipts for enterprise agent governance (AAR)](https://github.com/microsoft/autogen/issues/7353) (222 comments, state: open)
- Microsoft AutoGen: [Proposal: GuardrailProvider protocol for tool call interception](https://github.com/microsoft/autogen/issues/7405) (58 comments, state: open)
- Microsoft AutoGen: [[Feature] Governance extension for AutoGen — policy enforcement and agent identity](https://github.com/microsoft/autogen/issues/7613) (39 comments, state: closed)
- Dify: [[Refactor/Chore] use sqlite3 or Testcontainers to do sql test](https://github.com/langgenius/dify/issues/32454) (36 comments, state: open)

## Multi-agent disagreement and deadlock

Problem: Multi-agent systems often lack explicit conflict semantics and accountability for final decisions.

Frequency signal: 678 category hits across Coordination, Planning, Evaluation, Reliability.

Current solution: Manager-worker roles, round-robin chat, voting, critic agents, and handoffs.

Remaining gap: Multi-agent systems often lack explicit conflict semantics and accountability for final decisions.

Evidence examples:
- Microsoft AutoGen: [Feature: Cryptographic action receipts for enterprise agent governance (AAR)](https://github.com/microsoft/autogen/issues/7353) (222 comments, state: open)
- CrewAI: [[FEATURE]:Governance middleware hook for tool call authorization](https://github.com/crewAIInc/crewAI/issues/5888) (67 comments, state: open)
- Microsoft AutoGen: [Feature: Agent trust verification via MoltBridge for cross-org multi-agent scenarios](https://github.com/microsoft/autogen/issues/7525) (48 comments, state: open)
- Microsoft AutoGen: [Payment primitive for multi-agent systems - how are teams handling this?](https://github.com/microsoft/autogen/issues/7492) (39 comments, state: open)

## Memory pollution and stale state

Problem: Frameworks rarely estimate whether a memory will improve a future decision before writing or retrieving it.

Frequency signal: 614 category hits across Memory, Context, Reliability.

Current solution: Vector/graph memory layers, summarization, explicit memory blocks, and application-specific write policies.

Remaining gap: Frameworks rarely estimate whether a memory will improve a future decision before writing or retrieving it.

Evidence examples:
- CrewAI: [[Security] Memory content injected into system prompt without sanitization enables indirect prompt injection](https://github.com/crewAIInc/crewAI/issues/5057) (26 comments, state: open)
- Microsoft AutoGen: [Security: Add OWASP Agent Memory Guard to security docs (memory poisoning protection)](https://github.com/microsoft/autogen/issues/7683) (26 comments, state: open)
- Microsoft AutoGen: [RFC: Cross-agent shared memory store with on-demand capsule recall (agent/group/global scopes)](https://github.com/microsoft/autogen/issues/7748) (23 comments, state: open)
- LlamaIndex: [[Feature Request]: Memory poisoning defense (OWASP ASI06) integration for agent memory stores](https://github.com/run-llama/llama_index/issues/21666) (23 comments, state: open)

## Prompt sensitivity and hidden assumptions

Problem: Prompts encode assumptions that are rarely surfaced, tested, or updated as tasks change.

Frequency signal: 612 category hits across Hallucination, Planning, Evaluation, Reliability.

Current solution: Prompt templates, examples, validators, guardrails, and test suites.

Remaining gap: Prompts encode assumptions that are rarely surfaced, tested, or updated as tasks change.

Evidence examples:
- LangGraph: [Bug: PostgresStore numeric filter operators ($gt, $gte, $lt, $lte) use lexicographic (text) comparison instead of numeric comparison](https://github.com/langchain-ai/langgraph/issues/7684) (6 comments, state: open)
- Qwen-Agent: [coder.qwen.ai stale for more than an hour at "$ Initializing git repository..."](https://github.com/QwenLM/Qwen-Agent/issues/787) (6 comments, state: open)
- CrewAI: [bug: tool exceptions are caught and replaced with generic error messages — lose root cause](https://github.com/crewAIInc/crewAI/issues/6262) (4 comments, state: open)
- OpenHands: [[Bug]: Workers AI broken](https://github.com/OpenHands/OpenHands/issues/14398) (3 comments, state: open)

## Human approval bottlenecks

Problem: Human review is treated as a binary gate rather than a scarce resource to allocate by risk.

Frequency signal: 521 category hits across Human-in-the-loop, Safety, Latency, Workflow.

Current solution: Interrupts, approval steps, permissions, and manual checkpoints.

Remaining gap: Human review is treated as a binary gate rather than a scarce resource to allocate by risk.

Evidence examples:
- Microsoft AutoGen: [Payment primitive for multi-agent systems - how are teams handling this?](https://github.com/microsoft/autogen/issues/7492) (39 comments, state: open)
- Dify: [[Refactor/Chore] use sqlite3 or Testcontainers to do sql test](https://github.com/langgenius/dify/issues/32454) (36 comments, state: open)
- CrewAI: [[FEATURE] Runtime release-control mediation layer before agent/tool execution](https://github.com/crewAIInc/crewAI/issues/6025) (31 comments, state: open)
- LangGraph: [Docs safety guidance: auditable final-state receipts for agent completion claims?](https://github.com/langchain-ai/langgraph/issues/7844) (22 comments, state: open)

## Context explosion

Problem: Compression is often relevance-based, not decision-sensitive or risk-aware.

Frequency signal: 340 category hits across Context, Memory, Cost, Latency.

Current solution: Summaries, retrieval, context compression, and larger context windows.

Remaining gap: Compression is often relevance-based, not decision-sensitive or risk-aware.

Evidence examples:
- Dify: [[Refactor/Chore] use sqlite3 or Testcontainers to do sql test](https://github.com/langgenius/dify/issues/32454) (36 comments, state: open)
- CrewAI: [[Security] Memory content injected into system prompt without sanitization enables indirect prompt injection](https://github.com/crewAIInc/crewAI/issues/5057) (26 comments, state: open)
- OpenHands: [Security: OWASP Agent Memory Guard integration for memory poisoning defense](https://github.com/OpenHands/OpenHands/issues/14416) (21 comments, state: open)
- Microsoft AutoGen: [Architecture question: Handshake protocol for cross-runtime agent identification](https://github.com/microsoft/autogen/issues/7589) (21 comments, state: open)
