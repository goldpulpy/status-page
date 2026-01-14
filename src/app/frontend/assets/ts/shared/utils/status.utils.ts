import type {
  StatusComponent,
  GroupForStatus,
  IncidentForStatus,
} from "@/shared/types/api";
import { IncidentStatus } from "@/shared/types/incident";

export const isGroup = (
  component: StatusComponent,
): component is GroupForStatus => component.type === "group";

export const isActiveIncident = (incident: IncidentForStatus): boolean =>
  !incident.status || incident.status === IncidentStatus.OPEN;

export const formatIncidentDate = (dateString: string): string => {
  const date = new Date(dateString);
  return `${date.toDateString()} at ${date.toLocaleTimeString()}`;
};
