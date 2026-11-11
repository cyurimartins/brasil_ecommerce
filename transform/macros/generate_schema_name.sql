{#
  Usa o schema customizado como está (staging, intermediate, marts), em vez do
  padrão do dbt de concatenar com o schema do target (ex.: main_staging).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
