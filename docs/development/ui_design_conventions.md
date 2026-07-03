# SafeFlow UI Design And Implementation Conventions

Generated on: 2026-07-03

Purpose: keep SafeFlow UI work consistent while we build the P0 operator demo. This file is the source of truth for React/Vite interface decisions unless a product requirement explicitly overrides it.

## 1. Product UI Direction

SafeFlow is an enterprise operator console, not a marketing site.

The UI should feel:

- Operational: optimized for repeated workflow review, not first-time promotion.
- Dense but readable: more like an AWS console than a landing page.
- Evidence-first: state, timeline, policy, approval, and audit details must be visible without decorative filler.
- Predictable: primary actions, filters, status, and evidence panels should stay in stable places.
- Calm under risk: denied, approval, mismatch, and recovered-timeout cases should be clear without alarmist styling.

## 2. Reference Style

Use Amazon/AWS patterns as inspiration, not as a brand copy.

Useful references:

- Cloudscape Design System: https://cloudscape.design/
- AWS Management Console visual update: https://aws.amazon.com/blogs/aws/announcing-a-visual-update-to-the-aws-management-console-preview/
- AWS Systems Manager visual designer interface: https://docs.aws.amazon.com/systems-manager/latest/userguide/visual-designer-interface-overview.html
- Prime Video navigation simplification coverage: https://www.theverge.com/2024/7/23/24203748/amazon-prime-video-interface-update

Patterns to borrow:

- Strong search/filter/action zones.
- Clear page-level status.
- Container borders instead of heavy shadows.
- Compact cards and tables for scan speed.
- Tabs or segmented controls when a view has distinct modes.
- Context panels for details instead of long explanatory copy.
- Stable toolbar placement for contextual actions.
- Responsive layouts that preserve the main workflow, not just stack randomly.

Patterns to avoid:

- Amazon retail visual clutter.
- Marketing hero sections.
- Product-card e-commerce styling.
- Large decorative graphics.
- Copying Amazon colors, logos, nav bars, or trade dress.

## 3. Page Structure

Every operator screen should use this hierarchy:

1. Page header: product area, workflow title, global status, and top-level run/action button when applicable.
2. Control band: fixture selector, filters, search, scenario inputs, or benchmark controls.
3. Primary evidence area: result status, transition, metrics, approval state, and timeline.
4. Detail area: audit receipt, state diff/final state, raw JSON, logs, or benchmark breakdown.
5. Secondary tools: exports, reset, copy IDs, or debug toggles.

Do not create a landing page for P0. The first viewport should be the usable operator console.

## 4. Layout Rules

- Use constrained wide layouts for desktop: target max width around `1280px` to `1440px`.
- Prefer CSS grid for console panes and tables.
- Use 8px or smaller border radius for panels, cards, buttons, and inputs.
- Use borders as the main separation method. Avoid broad shadows except for transient overlays.
- Do not nest cards inside cards. Repeated records such as receipts, timeline rows, or metric tiles may be framed inside a panel.
- Keep controls aligned and stable. A run button, fixture selector, and status pill should not jump after results load.
- Long IDs, hashes, and JSON must wrap or scroll without resizing the surrounding layout.
- Empty states should be compact and factual.

## 5. Visual Tokens

Use a restrained enterprise palette.

Recommended base tokens:

```css
--sf-bg: #f5f7fa;
--sf-surface: #ffffff;
--sf-border: #d8e0ea;
--sf-border-soft: #e6edf4;
--sf-text: #1f2933;
--sf-text-muted: #5f6c7a;
--sf-action: #176b87;
--sf-success-bg: #eef8f3;
--sf-success-text: #14573c;
--sf-warning-bg: #fff8df;
--sf-warning-text: #74560c;
--sf-danger-bg: #fff4ed;
--sf-danger-text: #8a3b12;
```

Rules:

- Keep the UI mostly neutral, with color reserved for status, actions, and risk.
- Do not let the page become dominated by one hue family.
- Interactive blue/teal is acceptable for actions, but status colors must remain semantically distinct.
- Do not use gradients, glowing backgrounds, decorative blobs, or oversized illustrations in the console.

## 6. Typography

- Use system UI fonts or the existing app font stack.
- Do not scale font size with viewport width.
- Keep letter spacing at `0`, except short uppercase labels may use normal browser rendering with no negative spacing.
- Use compact but readable sizes:
  - Page title: `28px` to `32px`.
  - Panel title: `14px` to `16px`, bold.
  - Body/control text: `13px` to `15px`.
  - Metric labels: `11px` to `12px`, uppercase.
  - Code/JSON: `12px` to `13px`.
- Status, IDs, and hashes must be readable but should not overpower evidence content.

## 7. Components

### Buttons

- Use icon plus text for primary commands.
- Use icon-only buttons only for familiar binary or tool actions, and provide accessible labels when possible.
- Primary action: filled button using `--sf-action`.
- Risk action: use semantic danger styling.
- Disabled action: keep visible but muted.

### Selectors And Filters

- Use `select`, segmented controls, tabs, or search fields for mode/scenario changes.
- Fixture selection should be explicit; do not hide it behind a free-form text field.
- Filters should sit near the content they affect.

### Status Pills

- Every workflow status should map to a stable visual state:
  - `completed`, `completed_with_recovered_timeout`: success.
  - `approval_pending`, `pending_manual_review`: warning.
  - `denied`, `escalated_state_mismatch`, `failed_safe`: danger or blocked.
- Use text labels plus color. Never rely on color alone.

### Metrics

- Metric tiles should be compact and comparable.
- Put label above value.
- Avoid vanity metrics. For P0, show final state match, receipts, timeline count, transition, duplicate refund count, approval recall, and audit completeness when available.

### Timeline

- Timeline rows must show:
  - event type or outcome
  - short summary
  - receipt ID or state hash when present
- Use chronological order unless a task explicitly asks for grouping.
- Keep rows compact; timeline is for scanning, not prose.

### Audit Receipts

- Receipt cards or table rows must show:
  - action ID
  - outcome
  - intended transition
  - observed transition
  - pre/post state hashes
  - policy decision when space allows
- Use short hashes in summaries and full hashes in details or copyable raw JSON.

### State Evidence

- State panels must show either:
  - mismatch detail plus final state, or
  - pre/post diff plus final state.
- JSON blocks must scroll vertically and wrap long tokens.
- Do not bury mismatch details below unrelated logs.

## 8. Interaction Rules

- One primary action per panel.
- Running state must be visible on the triggering control.
- Errors should appear close to the control or panel that caused them.
- Approval actions must be visibly separate from run actions.
- Never show a refund success message while approval is pending or rejected.
- UI actions must call the API; do not simulate safety outcomes in frontend state.

## 9. Accessibility

- Use semantic elements: `main`, `section`, `button`, `label`, `select`, `textarea`, `table`, `dl`.
- Controls must have text labels or accessible labels.
- Status colors need text and icon support.
- Keyboard focus must remain visible.
- Avoid tiny click targets; icon buttons should be at least `36px` square.
- Maintain contrast for all status pills, inputs, and error messages.

## 10. Implementation Rules

- Keep UI state local until a shared need appears.
- Keep API payload types explicit in TypeScript.
- Do not put safety logic in the UI. The UI may display backend decisions and trigger approval endpoints only.
- Read API base URL from `VITE_API_BASE_URL`; backend CORS origins come from `SAFEFLOW_CORS_ORIGINS`.
- Prefer existing dependencies. Use `lucide-react` icons when an icon is needed.
- Avoid adding a component library during P0 unless the user explicitly approves it.
- CSS should use named classes and token-like variables before introducing CSS-in-JS.
- Keep UI copy short and operational; do not explain product features inside the app.

## 11. Responsive Rules

- Desktop: use multi-pane grid with request/result/timeline above details.
- Tablet: reduce to two columns while preserving request and result visibility.
- Mobile: stack panels in workflow order: status, request, result, timeline, audit, state.
- Text must not overlap or overflow controls.
- JSON and receipt panels should scroll internally instead of widening the viewport.

## 12. Testing Rules

Before marking a UI task done:

```bash
npm --prefix ui run lint
npm --prefix ui run build
```

If the UI calls the API, also run:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
npm --prefix ui run dev -- --host 127.0.0.1 --port 5173
```

Then verify in a real browser with Playwright or manual browser testing:

- The app renders on first load.
- A happy-path fixture runs successfully.
- At least one risk case renders correctly: approval pending, denied, mismatch, or recovered timeout.
- Timeline, audit receipts, and state evidence are visible.
- No text overlaps at desktop and mobile widths.

Record the commands and browser scenario in the task completion note.

## 13. Current UI Direction For SafeFlow

The current P0 console should evolve toward an AWS-console-like operator workspace:

- Top header with status and environment.
- Left or top control area for fixture/request selection.
- Center result and timeline area.
- Right or lower details area for audit/state evidence.
- Optional future tabs: Workflow, Audit, Evaluation, Baseline.
- Optional future toolbar: Run, Reset, Export JSON, Copy Workflow ID.

Keep the first screen useful for a hackathon judge: they should immediately see what was run, what decision SafeFlow made, why it was safe, and which evidence proves it.
