# Databricks notebook source
# MAGIC %md
# MAGIC # Provisionamento da persistência do T-DAS
# MAGIC
# MAGIC Cria schema, Unity Catalog Volume e tabelas Delta para testes salvos, versões imutáveis e auditoria.
# MAGIC Execute em um workspace de desenvolvimento com Unity Catalog habilitado. Confirme catálogo e permissões com o administrador antes de usar em produção.
# MAGIC
# MAGIC **Idempotência:** as instruções usam `IF NOT EXISTS`; executar novamente não apaga nem substitui dados.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parâmetros
# MAGIC Ajuste os valores abaixo antes de executar. O catálogo de exemplo é `eng_lab`; o schema e o volume são dedicados à aplicação.

# COMMAND ----------

dbutils.widgets.text("catalog", "eng_lab", "Catálogo")
dbutils.widgets.text("schema", "tdas_app", "Schema da aplicação")
dbutils.widgets.text("volume", "tdas_files", "Volume")

catalog = dbutils.widgets.get("catalog").strip()
schema = dbutils.widgets.get("schema").strip()
volume = dbutils.widgets.get("volume").strip()

def quote_identifier(value: str) -> str:
    """Quote one Unity Catalog identifier and reject empty input."""
    if not value:
        raise ValueError("Catálogo, schema e volume não podem ficar vazios.")
    return "`" + value.replace("`", "``") + "`"

catalog_q = quote_identifier(catalog)
schema_q = quote_identifier(schema)
volume_q = quote_identifier(volume)
namespace = f"{catalog_q}.{schema_q}"

print(f"Alvo: {catalog}.{schema} (volume {volume})")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Schema e volume
# MAGIC O volume guarda originais e Parquet processado, organizados por `test_id` e versão. Não remova o volume em uma execução de manutenção.

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {namespace}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {namespace}.{volume_q}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Tabelas Delta
# MAGIC As chaves são lógicas. A aplicação deve garantir idempotência e concorrência; não deve depender de constraints de chave primária para impedir duplicação.

# COMMAND ----------

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {namespace}.tests (
  test_id STRING NOT NULL COMMENT 'UUID estável do teste',
  title STRING NOT NULL COMMENT 'Nome exibido na listagem',
  project STRING,
  test_type STRING,
  vehicle_type STRING,
  test_date DATE,
  current_version INT NOT NULL,
  status STRING NOT NULL COMMENT 'ACTIVE ou DELETED',
  metadata_json STRING COMMENT 'Metadados opcionais não promovidos a colunas',
  created_by STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_by STRING NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  deleted_by STRING,
  deleted_at TIMESTAMP
) USING DELTA
COMMENT 'Estado atual e campos de busca dos testes T-DAS'
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {namespace}.test_versions (
  test_id STRING NOT NULL,
  version_no INT NOT NULL,
  saved_at TIMESTAMP NOT NULL,
  saved_by STRING NOT NULL,
  change_reason STRING,
  processing_config_json STRING COMMENT 'Opções usadas no processamento',
  metadata_json STRING COMMENT 'Snapshot completo dos metadados da versão',
  processed_data_path STRING NOT NULL COMMENT 'Caminho do Parquet no Unity Catalog Volume',
  source_file_path STRING COMMENT 'Caminho do arquivo original no Volume, se retido',
  source_file_name STRING,
  source_checksum STRING,
  base_version INT COMMENT 'Versão aberta como base da edição; útil para controle otimista',
  write_status STRING NOT NULL COMMENT 'COMPLETED ou INCOMPLETE para recuperação de falhas'
) USING DELTA
COMMENT 'Snapshots imutáveis de cada versão dos testes T-DAS'
""")

spark.sql(f"""
CREATE TABLE IF NOT EXISTS {namespace}.audit_events (
  event_id STRING NOT NULL,
  test_id STRING NOT NULL,
  version_no INT,
  action STRING NOT NULL COMMENT 'CREATED, UPDATED, DELETED ou RESTORED',
  actor STRING NOT NULL,
  occurred_at TIMESTAMP NOT NULL,
  changed_fields_json STRING,
  before_json STRING,
  after_json STRING,
  reason STRING
) USING DELTA
COMMENT 'Trilha de auditoria das operações realizadas pela aplicação T-DAS'
""")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificação estrutural
# MAGIC Exibe os objetos criados para inspeção no workspace. A validação de leitura/gravação deve ser executada com a identidade configurada para o Databricks App.

# COMMAND ----------

for object_name in ("tests", "test_versions", "audit_events"):
    full_name = f"{catalog}.{schema}.{object_name}"
    print(f"\\n{full_name}")
    spark.sql(f"DESCRIBE TABLE {namespace}.{quote_identifier(object_name)}").show(truncate=False)

print(f"\\nVolume: /Volumes/{catalog}/{schema}/{volume}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Permissões (aplicar separadamente)
# MAGIC Conceda ao principal da identidade do Databricks App somente o necessário. A administração deve substituir `<app_service_principal>` pelo nome ou ID aceito pelo workspace e executar os comandos após revisar a política local.
# MAGIC
# MAGIC ```sql
# MAGIC GRANT USE CATALOG ON CATALOG eng_lab TO `<app_service_principal>`;
# MAGIC GRANT USE SCHEMA ON SCHEMA eng_lab.tdas_app TO `<app_service_principal>`;
# MAGIC GRANT SELECT, MODIFY ON TABLE eng_lab.tdas_app.tests TO `<app_service_principal>`;
# MAGIC GRANT SELECT, MODIFY ON TABLE eng_lab.tdas_app.test_versions TO `<app_service_principal>`;
# MAGIC GRANT SELECT, MODIFY ON TABLE eng_lab.tdas_app.audit_events TO `<app_service_principal>`;
# MAGIC GRANT READ VOLUME, WRITE VOLUME ON VOLUME eng_lab.tdas_app.tdas_files TO `<app_service_principal>`;
# MAGIC ```
# MAGIC
# MAGIC Ajuste o catálogo/schema/volume desses exemplos se os widgets tiverem outros valores. A identidade também pode precisar de `USE CATALOG` e `USE SCHEMA` conforme a configuração do Unity Catalog.
