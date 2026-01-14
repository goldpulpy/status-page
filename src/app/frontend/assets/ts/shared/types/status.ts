import { OPERATIONAL_STATUS } from "@/shared/constants";
import type {
  GroupForStatus,
  IncidentForStatus,
  MonitorForStatus,
} from "@/shared/types/api";

export interface Tooltip {
  isActive: boolean;
  incidents?: EnrichedIncident[];
  style: string;
}

export interface IncidentConfig {
  color: string;
  bgColor: string;
  borderColor: string;
  title: string;
}

export interface EnrichedIncident extends IncidentForStatus, IncidentConfig {
  message: string;
  tooltip: string;
}

export interface Days {
  color: string;
  index: number;
  incidents?: EnrichedIncident[];
}

export interface EnrichedMonitor extends MonitorForStatus {
  currentIncident: EnrichedIncident | typeof OPERATIONAL_STATUS;
  history: Days[];
}

export interface EnrichedGroup extends GroupForStatus {
  monitors: EnrichedMonitor[];
}

export type EnrichedStatusComponent = EnrichedMonitor | EnrichedGroup;
