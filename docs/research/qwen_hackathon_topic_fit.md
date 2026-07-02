# Qwen Hackathon Topic Fit

Generated on: 2026-06-30

This file reframes the research findings as hackathon-ready topics. The goal is not to improve agents in the abstract, but to use Qwen Cloud to solve real-world problems across the official tracks.

## Best-Fit Topics

| Priority | Topic | Primary Track | Real-World Problem | How Qwen Is Used | Why It Fits |
| ---: | --- | --- | --- | --- | --- |
| 1 | Safe Customer Support Autopilot | Track 4: Autopilot Agent | Support teams need to answer emails, inspect orders, issue refunds, and escalate risky cases without duplicate or unauthorized actions. | Qwen understands customer emails, extracts intent, checks policy, chooses tools, drafts response, and decides whether human approval is needed. | End-to-end business workflow, ambiguous inputs, external tools, human-in-the-loop, production-readiness. |
| 2 | Sales Quote Autopilot | Track 4: Autopilot Agent | Sales teams spend time converting inbound inquiries into compliant quotes while avoiding wrong pricing, invalid discounts, and missing approvals. | Qwen reads inquiry emails, extracts requirements, checks CRM/pricing tools, generates quote, and routes risky discounts to humans. | Strong business value, clear workflow automation, measurable time saved. |
| 3 | IT Incident Remediation Autopilot | Track 4: Autopilot Agent | SRE/IT teams receive alerts and need triage, diagnosis, safe remediation, and escalation without unsafe production changes. | Qwen summarizes alerts/logs, selects diagnostic tools, proposes or runs safe remediation, and requests approval for risky actions. | Production-oriented, tool-heavy, high-value, easy to show safety checkpoints. |
| 4 | Persistent Account Memory Support Agent | Track 1: MemoryAgent | Customer-facing agents forget preferences, account context, previous complaints, and outdated facts across sessions. | Qwen uses persistent memory to recall critical customer/account facts, forget stale information, and personalize decisions. | Directly matches memory storage, retrieval, forgetting, and limited context requirements. |
| 5 | Multi-Agent Business Workflow Team | Track 3: Agent Society | Complex business workflows need multiple roles: intake, policy, pricing, compliance, execution, and customer response. | Qwen powers specialized agents that negotiate, resolve conflicts, and compare efficiency against a single-agent baseline. | Directly matches task division, dialogue, disagreement resolution, and measurable gain. |
| 6 | HR Screening And Interview Scheduler | Track 4: Autopilot Agent | Recruiters need to screen resumes, match role requirements, avoid policy-sensitive mistakes, and schedule interviews. | Qwen parses resumes/job descriptions, ranks fit with explanations, drafts interview plans, and uses calendar/email tools. | Practical workflow, human checkpoints, useful but must handle fairness/privacy carefully. |
| 7 | Invoice Or Vendor Payment Autopilot | Track 4: Autopilot Agent | Finance teams need to process invoice/payment requests while avoiding duplicate payments and unauthorized approvals. | Qwen extracts invoice data, checks vendor state, detects duplicates, prepares payment request, and escalates irreversible actions. | Very industrial and high-stakes, but harder to demo safely. |
| 8 | Edge Maintenance Assistant | Track 5: EdgeAgent | Field devices need local perception and cloud reasoning for maintenance under weak networks. | Qwen reasons over sensor summaries/images/logs and sends local actions or technician instructions. | Fits EdgeAgent, but requires hardware/edge simulation effort. |

## Recommended Topic

**Safe Customer Support Autopilot**

Primary track:

**Track 4: Autopilot Agent**

Why this is the best fit:

- It is a real business workflow, not an abstract agent improvement.
- It naturally uses Qwen for language understanding, reasoning, tool selection, policy checking, and response generation.
- It demonstrates ambiguous input handling through messy customer emails.
- It invokes external tools such as order lookup, refund API, CRM update, email drafting, and ticket escalation.
- It includes human-in-the-loop checkpoints for refunds, policy exceptions, angry customers, high-value accounts, and irreversible actions.
- It can show production-readiness through audit logs, state validation, idempotency checks, and approval gates.
- It can be implemented in 10-12 days with mock business APIs and Alibaba Cloud deployment.

## Differentiator

The differentiator should not be described as "we improved agents."

Describe it as:

**The Autopilot does not merely call tools. It verifies the expected business state transition before and after every critical action.**

Example:

- User email: "I was charged twice. Refund me now."
- Qwen extracts intent and ambiguity.
- The agent checks order/payment history.
- It identifies the required state transition: `payment_status: duplicated -> refund_pending` or `refund_completed`.
- It checks whether the refund action is allowed by policy.
- If high-risk, it asks for human approval.
- If approved, it calls the refund tool with an idempotency key.
- It verifies that the final state changed exactly once.
- It drafts the customer response and writes an audit receipt.

## Track 4 Submission Story

Title:

**SafeFlow: Qwen Autopilot for Safe Customer Support Actions**

One-line description:

**SafeFlow automates customer support workflows from messy emails to verified business actions, using Qwen to reason over intent, policy, tools, memory, and human approval checkpoints.**

Core features:

- Email/ticket intent extraction.
- Account/order lookup.
- Policy-aware decision making.
- State-transition-aware tool execution.
- Human approval for risky actions.
- Duplicate side-effect prevention.
- Final-state verification.
- Audit receipt for every action.

Measurable demo:

- Baseline agent calls refund/email/update tools directly and can duplicate side effects.
- SafeFlow validates state transitions and prevents duplicate or unauthorized actions.
- Metrics: task success rate, duplicate action count, unnecessary human approval count, final-state correctness, and average steps per case.

## Secondary Track Variants

### Track 1: MemoryAgent Variant

Topic:

**Persistent Customer Memory Agent**

Use this if you want the project to focus on cross-session memory.

Real-world problem:

Support agents forget customer preferences, past complaints, product history, or outdated account facts.

Main challenge:

Efficiently store, retrieve, update, and forget memories under limited context.

### Track 3: Agent Society Variant

Topic:

**Multi-Agent Support Operations Team**

Use this if you want a more visibly multi-agent system.

Agents:

- Intake Agent.
- Policy Agent.
- Account State Agent.
- Resolution Agent.
- Approval Agent.
- Customer Response Agent.

Main challenge:

Resolve disagreement between policy, customer emotion, account state, and business cost.

### Track 5: EdgeAgent Variant

Topic:

**Edge Maintenance Autopilot**

Use this only if you can simulate or build edge input.

Real-world problem:

Factories, stores, or devices need maintenance decisions under limited connectivity.

Main challenge:

Local sensor perception plus Qwen Cloud reasoning with graceful degradation.

## Final Recommendation

Build for **Track 4: Autopilot Agent**.

The most competition-aligned topic is:

**SafeFlow: Qwen Autopilot for Safe Customer Support Actions**

This turns the earlier research gap into a real-world business workflow. The state-transition mechanism becomes the production-readiness feature, not the whole project.
