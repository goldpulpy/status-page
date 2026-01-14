import { BaseIncident } from "@/shared/types/incident";
import { MonitorForm } from "./monitor";

export interface GroupForCRUD {
  id: string;
  name: string;
}

export interface MonitorForCRUD extends MonitorForm {
  id: string;
}

export interface IncidentForStatus extends BaseIncident {
  id: string;
  message: string;
  created_at: string;
  ended_at: string | null;
}

export interface MonitorForStatus {
  type: string;
  id: string;
  name: string;
  incidents: IncidentForStatus[];
  created_at: string;
}

export interface GroupForStatus {
  type: string;
  id: string;
  name: string;
  monitors: MonitorForStatus[];
}

export type StatusComponent = MonitorForStatus | GroupForStatus;
