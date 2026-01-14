import { MonitorForCRUD } from "@/shared/types/api";

export interface MonitorForm {
  name: string;
  type: string;
  endpoint: string;
  group_id: string | null;
  method: string | null;
  headers: string | null;
  request_body: string | null;
  expected_response_code: number | null;
  expected_content_pattern: string | null;
  latency_threshold_ms: number | null;
  error_mapping: string | null;
}

export interface EnrichedMonitor extends MonitorForCRUD {
  group_name: string;
}
