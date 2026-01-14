import { IncidentType } from "@/shared/types/incident";
import { MonitorForm } from "@/shared/types/monitor";
import type { IncidentConfig } from "@/shared/types/status";

export const EMPTY_MONITOR_FORM: MonitorForm = {
  name: "",
  group_id: null,
  endpoint: "",
  method: null,
  type: "HTTP",
  headers: null,
  request_body: null,
  expected_response_code: 200,
  expected_content_pattern: null,
  latency_threshold_ms: 1000,
  error_mapping: null,
};

export const NO_GROUP = "No group";

export const INCIDENT_CONFIG: Record<IncidentType, IncidentConfig> = {
  [IncidentType.MAJOR_OUTAGE]: {
    color: "bg-major-outage",
    bgColor: "bg-major-outage/20",
    borderColor: "border-major-outage",
    title: "Major service outage",
  },
  [IncidentType.PARTIAL_OUTAGE]: {
    color: "bg-partial-outage",
    bgColor: "bg-partial-outage/20",
    borderColor: "border-partial-outage",
    title: "Partial service disruption",
  },
  [IncidentType.DEGRADED]: {
    color: "bg-degraded",
    bgColor: "bg-degraded/20",
    borderColor: "border-degraded",
    title: "Performance degradation detected",
  },
} as const;

export const OPERATIONAL_STATUS = {
  type: "operational",
  color: "bg-operational",
  bgColor: "bg-operational/20",
  borderColor: "border-operational",
  status: "operational",
  title: "All systems operational",
  message: "No active incidents",
} as const;

export const REFRESH_INTERVAL_MS = 20_000;

export const INCIDENT_PRIORITY_ORDER: readonly IncidentType[] = [
  IncidentType.MAJOR_OUTAGE,
  IncidentType.PARTIAL_OUTAGE,
  IncidentType.DEGRADED,
] as const;
