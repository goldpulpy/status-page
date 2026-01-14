export enum IncidentStatus {
  OPEN = "open",
  RESOLVED = "resolved",
}

export enum IncidentType {
  MAJOR_OUTAGE = "major_outage",
  PARTIAL_OUTAGE = "partial_outage",
  DEGRADED = "degraded",
}

export interface BaseIncident {
  status: IncidentStatus;
  type: IncidentType;
}
