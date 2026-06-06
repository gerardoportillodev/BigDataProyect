#!/usr/bin/env bash

set -euo pipefail

export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-arm64}"
export HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
export SPARK_HOME="${SPARK_HOME:-/opt/spark}"
export HADOOP_CONF_DIR="${HADOOP_CONF_DIR:-$HADOOP_HOME/etc/hadoop}"
export PATH="$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$SPARK_HOME/bin:$SPARK_HOME/sbin"

if [ ! -f /hadoop/dfs/name/current/VERSION ]; then
  hdfs namenode -format -force -nonInteractive
fi

hdfs --daemon start namenode
hdfs --daemon start datanode

for _ in $(seq 1 30); do
  if hdfs dfs -ls / >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "HDFS disponible en hdfs://bigdata:9000"
echo "NameNode UI disponible en http://localhost:9870"

tail -f /dev/null
