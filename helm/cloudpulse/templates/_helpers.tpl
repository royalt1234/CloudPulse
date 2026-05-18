{{/*
  Expand the name of the chart.
*/}}
{{- define "cloudpulse.name" -}}
{{- .Chart.Name }}
{{- end }}

{{/*
  Full image path helper: registry/image:tag
*/}}
{{- define "cloudpulse.image" -}}
{{- $reg := .ctx.Values.global.imageRegistry -}}
{{- if $reg -}}
{{ $reg }}/{{ .image }}:{{ .ctx.Values.global.imageTag }}
{{- else -}}
{{ .image }}:{{ .ctx.Values.global.imageTag }}
{{- end }}
{{- end }}

{{/*
  Common labels
*/}}
{{- define "cloudpulse.labels" -}}
app.kubernetes.io/managed-by: Helm
app.kubernetes.io/part-of: cloudpulse
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}
