import { parseISO, startOfDay, endOfDay, subDays, isBefore } from "date-fns";
import type {
  IncidentForStatus,
  MonitorForStatus,
  StatusComponent,
} from "@/shared/types/api";
import type {
  Days,
  EnrichedIncident,
  EnrichedStatusComponent,
} from "@/shared/types/status";
import {
  INCIDENT_CONFIG,
  INCIDENT_PRIORITY_ORDER,
  OPERATIONAL_STATUS,
} from "@/shared/constants";
import { isGroup } from "@/shared/utils/status.utils";
import { BaseIncident, IncidentStatus } from "@/shared/types/incident";

const HISTORY_DAYS = 30;
const HISTORY_OFFSET = HISTORY_DAYS - 1;

export class StatusProcessor {
  buildEnrichedIncidents(
    components: StatusComponent[],
  ): Map<string, EnrichedIncident[]> {
    const enrichedIncidentsByMonitor = new Map();
    components.forEach((component) => {
      const monitors = isGroup(component) ? component.monitors : [component];
      monitors.forEach((monitor) => {
        const incidents = monitor.incidents.map((incident) =>
          this.buildIncident(monitor, incident),
        );
        enrichedIncidentsByMonitor.set(monitor.id, incidents);
      });
    });

    return enrichedIncidentsByMonitor;
  }

  buildEnrichedStatusComponent(
    components: StatusComponent[],
    enrichedIncidentsByMonitor: Map<string, EnrichedIncident[]>,
  ): EnrichedStatusComponent[] {
    return components.map((component) => {
      if (isGroup(component)) {
        return {
          ...component,
          monitors: component.monitors.map((monitor) => ({
            ...monitor,
            currentIncident: this.findActiveIncident(
              enrichedIncidentsByMonitor.get(monitor.id) ?? [],
            ),
            history: this.buildHistoryForMonitors([monitor]),
          })),
        };
      } else {
        return {
          ...component,
          currentIncident: this.findActiveIncident(
            enrichedIncidentsByMonitor.get(component.id) ?? [],
          ),
          history: this.buildHistoryForMonitors([component]),
        };
      }
    });
  }

  findActiveIncident<T extends BaseIncident>(
    incidents: T[],
  ): T | typeof OPERATIONAL_STATUS {
    const prioritizedIncidents = this.getPrioritizedIncidents(incidents);
    const activeIncident = prioritizedIncidents.find(
      (inc) => inc.status === IncidentStatus.OPEN,
    );

    return activeIncident ?? OPERATIONAL_STATUS;
  }

  private getPrioritizedIncidents<T extends BaseIncident>(incidents: T[]): T[] {
    return [...incidents].sort(
      (a, b) =>
        INCIDENT_PRIORITY_ORDER.indexOf(a.type) -
        INCIDENT_PRIORITY_ORDER.indexOf(b.type),
    );
  }

  private sortIncidentsByDate(
    incidents: EnrichedIncident[],
  ): EnrichedIncident[] {
    return [...incidents].sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }

  private buildHistoryForMonitors(monitors: MonitorForStatus[]): Days[] {
    const now = new Date();

    return Array.from({ length: HISTORY_DAYS }, (_, dayIndex) => {
      const day = subDays(now, HISTORY_OFFSET - dayIndex);
      const dayStart = startOfDay(day);
      const dayEnd = endOfDay(day);

      const hasActiveMonitor = monitors.some((monitor) => {
        const componentCreated = parseISO(monitor.created_at);
        return !isBefore(dayEnd, componentCreated);
      });

      if (!hasActiveMonitor) {
        return { color: "bg-empty", index: dayIndex };
      }

      const dayIncidents: EnrichedIncident[] = [];
      for (const monitor of monitors) {
        for (const incident of monitor.incidents) {
          const incidentStartDate = parseISO(incident.created_at);
          const incidentEndDate = incident.ended_at
            ? parseISO(incident.ended_at)
            : null;

          const startedBeforeOrDuringDay = !isBefore(dayEnd, incidentStartDate);
          const endedAfterDay =
            !incidentEndDate || !isBefore(incidentEndDate, dayStart);

          if (startedBeforeOrDuringDay && endedAfterDay) {
            const enrichedIncident = this.buildIncident(monitor, incident);
            dayIncidents.push(enrichedIncident);
          }
        }
      }

      if (dayIncidents.length === 0) {
        return {
          color: "bg-operational",
          index: dayIndex,
          incidents: [],
        };
      }

      const prioritizedIncidents = this.getPrioritizedIncidents(dayIncidents);

      return {
        index: dayIndex,
        color: prioritizedIncidents[0].color,
        incidents: this.sortIncidentsByDate(prioritizedIncidents),
      };
    });
  }

  private buildIncident(
    monitor: MonitorForStatus,
    incident: IncidentForStatus,
  ): EnrichedIncident {
    const config = INCIDENT_CONFIG[incident.type];
    const startedDateTime = new Date(incident.created_at);
    const startedDate = startedDateTime.toLocaleDateString("en-US", {
      month: "long",
      day: "numeric",
    });
    const startedTime = startedDateTime.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    });

    const endedDateTime = incident.ended_at
      ? new Date(incident.ended_at)
      : null;

    const endedTime =
      endedDateTime?.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      }) ?? null;

    if (!config) {
      throw new Error(`Unknown incident type: ${incident.type}`);
    }

    return {
      ...incident,
      ...config,
      message: `${monitor.name} is currently affected. Issue started on ${startedDate} at ${startedTime}`,
      tooltip: incident.ended_at
        ? `${incident.message} (${startedTime} - ${endedTime})`
        : `${incident.message}`,
    };
  }
}
