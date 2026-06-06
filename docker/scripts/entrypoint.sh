#!/usr/bin/env bash

set -euo pipefail

export JAVA_HOME="${JAVA_HOME:-/opt/java}"
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
export SPARK_HOME="${SPARK_HOME:-/opt/spark}"
export HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-$HADOOP_HOME/etc/hadoop}"
export PATH="$PATH:$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$SPARK_HOME/sbin"

ROLE="${SERVICE_ROLE:-client}"

echo "Iniciando servicio con rol: ${ROLE}"

case "$ROLE" in
  namenode)
    if [ ! -f /hadoop/dfs/name/current/VERSION ]; then
      echo "Formateando NameNode por primera vez..."
      hdfs namenode -format -force -nonInteractive
    fi
    exec hdfs namenode
    ;;

  datanode)
    exec hdfs datanode
    ;;

  spark-master)
    exec "$SPARK_HOME/bin/spark-class" \
      org.apache.spark.deploy.master.Master \
      --host "${SPARK_MASTER_HOST:-spark-master}" \
      --port "${SPARK_MASTER_PORT:-7077}" \
      --webui-port "${SPARK_MASTER_WEBUI_PORT:-8080}"
    ;;

  spark-worker)
    exec "$SPARK_HOME/bin/spark-class" \
      org.apache.spark.deploy.worker.Worker \
      "${SPARK_MASTER_URL:-spark://spark-master:7077}" \
      --host "${SPARK_WORKER_HOSTNAME:-$(hostname)}" \
      --cores "${SPARK_WORKER_CORES:-2}" \
      --memory "${SPARK_WORKER_MEMORY:-2g}" \
      --webui-port "${SPARK_WORKER_WEBUI_PORT:-8081}"
    ;;

  client)
    echo "Contenedor cliente listo. HDFS: ${HDFS_URI:-hdfs://namenode:9000}; Spark: ${SPARK_MASTER_URL:-spark://spark-master:7077}"
    exec tail -f /dev/null
    ;;

  *)
    echo "SERVICE_ROLE desconocido: ${ROLE}" >&2
    exit 2
    ;;
esac
