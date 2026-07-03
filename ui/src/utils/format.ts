import { AlertTriangle, CheckCircle2, Clock3, XCircle } from "lucide-react";
import { createElement } from "react";

export function formatStatus(value: string | null | undefined): string {
  return value ? value.split("_").join(" ") : "none";
}

export function shortHash(value: string | null | undefined): string {
  return value ? value.slice(0, 10) : "none";
}

export function pct(v: number): string {
  return `${(v * 100).toFixed(1)}%`;
}

export function statusIcon(status: string) {
  if (status.includes("completed")) return createElement(CheckCircle2, { size: 18 });
  if (status.includes("pending")) return createElement(Clock3, { size: 18 });
  if (status.includes("denied") || status.includes("mismatch"))
    return createElement(AlertTriangle, { size: 18 });
  return createElement(XCircle, { size: 18 });
}
