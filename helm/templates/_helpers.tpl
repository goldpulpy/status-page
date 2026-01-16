{{/*
Expand the name of the chart.
*/}}
{{- define "status-page.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "status-page.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "status-page.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "status-page.labels" -}}
helm.sh/chart: {{ include "status-page.chart" . }}
{{ include "status-page.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "status-page.selectorLabels" -}}
app.kubernetes.io/name: {{ include "status-page.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "status-page.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "status-page.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the postgres image name
*/}}
{{- define "status-page.postgres.image" -}}
{{- $registry := .Values.postgres.image.registry | default "" | toString | trim -}}
{{- $repository := .Values.postgres.image.repository -}}
{{- $tag := .Values.postgres.image.tag | toString -}}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else }}
{{- printf "%s:%s" $repository $tag -}}
{{- end }}
{{- end }}

{{/*
PostgreSQL host
*/}}
{{- define "status-page.postgres.host" -}}
{{- if .Values.postgres.enabled }}
{{- printf "%s-postgres" (include "status-page.fullname" .) }}
{{- else if .Values.postgres.external.enabled }}
{{- .Values.postgres.external.host }}
{{- end }}
{{- end }}

{{/*
PostgreSQL port
*/}}
{{- define "status-page.postgres.port" -}}
{{- if .Values.postgres.enabled }}
{{- print "5432" }}
{{- else if .Values.postgres.external.enabled }}
{{- .Values.postgres.external.port | default "5432" }}
{{- end }}
{{- end }}

{{/*
PostgreSQL database
*/}}
{{- define "status-page.postgres.database" -}}
{{- if .Values.postgres.enabled }}
{{- .Values.postgres.auth.database }}
{{- else if .Values.postgres.external.enabled }}
{{- .Values.postgres.external.database }}
{{- end }}
{{- end }}

{{/*
PostgreSQL username
*/}}
{{- define "status-page.postgres.username" -}}
{{- if .Values.postgres.enabled }}
{{- .Values.postgres.auth.username }}
{{- else if .Values.postgres.external.enabled }}
{{- .Values.postgres.external.username }}
{{- end }}
{{- end }}

{{/*
PostgreSQL secret name
*/}}
{{- define "status-page.postgres.secretName" -}}
{{- if .Values.postgres.enabled }}
{{- if .Values.postgres.auth.existingSecret }}
{{- .Values.postgres.auth.existingSecret }}
{{- else }}
{{- printf "%s-postgres" (include "status-page.fullname" .) }}
{{- end }}
{{- else if .Values.postgres.external.enabled }}
{{- if .Values.postgres.external.existingSecret }}
{{- .Values.postgres.external.existingSecret }}
{{- else }}
{{- printf "%s-postgres" (include "status-page.fullname" .) }}
{{- end }}
{{- end }}
{{- end }}

{{/*
PostgreSQL secret key
*/}}
{{- define "status-page.postgres.secretKey" -}}
{{- if .Values.postgres.enabled }}
{{- if .Values.postgres.auth.existingSecret }}
{{- .Values.postgres.auth.passwordKey }}
{{- else }}
{{- printf "password" -}}
{{- end }}
{{- else if .Values.postgres.external.enabled }}
{{- if .Values.postgres.external.existingSecret }}
{{- .Values.postgres.external.passwordKey }}
{{- else }}
{{- printf "password" -}}
{{- end }}
{{- end }}
{{- end }}


{{/*
Application secrets name
*/}}
{{- define "status-page.secretName" -}}
{{- if .Values.secrets.existingSecret }}
{{- .Values.secrets.existingSecret }}
{{- else }}
{{- include "status-page.fullname" . }}-secrets
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "status-page.image" -}}
{{- $registry := .Values.image.registry | default "" | toString | trim -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | toString -}}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else }}
{{- printf "%s:%s" $repository $tag -}}
{{- end }}
{{- end }}
