{{- define "mainIngress.fullName" -}}
{{ .Values.env }}-{{ .Values.appName }}
{{- end -}}

{{- define "mainIngress.hostUrl" -}}
{{ include "mainIngress.fullName" . }}.endpoints.{{ .Values.gcpProjectName }}.cloud.goog
{{- end -}}
