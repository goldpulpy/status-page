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
const MS_PER_DAY = 24 * 60 * 60 * 1000;

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

  private buildHistoryForMonitors(monitors: MonitorForStatus[]): Days[] {
    const now = new Date();
    const startDate = subDays(now, HISTORY_OFFSET);

    const incidentsByDay = this.indexIncidentsByDay(monitors, startDate);

    return Array.from({ length: HISTORY_DAYS }, (_, dayIndex) => {
      const day = subDays(now, HISTORY_OFFSET - dayIndex);
      const dayEnd = endOfDay(day);

      const hasActiveMonitor = monitors.some((monitor) => {
        const componentCreated = parseISO(monitor.created_at);
        return !isBefore(dayEnd, componentCreated);
      });

      if (!hasActiveMonitor) {
        return { color: "bg-empty", index: dayIndex };
      }
      const dayIncidents = incidentsByDay.get(dayIndex) ?? [];

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
        incidents: prioritizedIncidents,
      };
    });
  }

  private indexIncidentsByDay(
    monitors: MonitorForStatus[],
    startDate: Date,
  ): Map<number, EnrichedIncident[]> {
    const incidentsByDay = new Map<number, EnrichedIncident[]>();
    const startTime = startOfDay(startDate).getTime();

    for (const monitor of monitors) {
      for (const incident of monitor.incidents) {
        const incidentDate = parseISO(incident.created_at);
        const dayIndex = Math.floor(
          (incidentDate.getTime() - startTime) / MS_PER_DAY,
        );

        if (dayIndex < 0 || dayIndex >= HISTORY_DAYS) {
          continue;
        }

        const enrichedIncident = this.buildIncident(monitor, incident);

        if (!incidentsByDay.has(dayIndex)) {
          incidentsByDay.set(dayIndex, []);
        }
        incidentsByDay.get(dayIndex)!.push(enrichedIncident);
      }
    }

    return incidentsByDay;
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
