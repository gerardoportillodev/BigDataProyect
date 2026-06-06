FROM python:3.11-slim-bookworm

ARG HADOOP_VERSION=3.3.6
ARG SPARK_VERSION=3.5.3

ENV DEBIAN_FRONTEND=noninteractive
ENV HADOOP_HOME=/opt/hadoop
ENV SPARK_HOME=/opt/spark
ENV HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
ENV PYSPARK_PYTHON=python3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       bash \
       ca-certificates \
       curl \
       openjdk-17-jdk \
       procps \
       tini \
    && JAVA_BIN="$(readlink -f "$(command -v java)")" \
    && JAVA_HOME_VAL="$(dirname "$(dirname "$JAVA_BIN")")" \
    && echo "JAVA_HOME=${JAVA_HOME_VAL}" >> /etc/environment \
    && ln -sfn "$JAVA_HOME_VAL" /opt/java \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/opt/java
ENV PATH=/opt/java/bin:${HADOOP_HOME}/bin:${HADOOP_HOME}/sbin:${SPARK_HOME}/bin:${SPARK_HOME}/sbin:${PATH}

RUN curl -fsSL "https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" \
      | tar -xz -C /opt \
    && mv "/opt/hadoop-${HADOOP_VERSION}" "$HADOOP_HOME" \
    && curl -fsSL "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" \
      | tar -xz -C /opt \
    && mv "/opt/spark-${SPARK_VERSION}-bin-hadoop3" "$SPARK_HOME"

COPY docker/hadoop/core-site.xml $HADOOP_CONF_DIR/core-site.xml
COPY docker/hadoop/hdfs-site.xml $HADOOP_CONF_DIR/hdfs-site.xml
COPY docker/scripts/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && mkdir -p /hadoop/dfs/name /hadoop/dfs/data /workspace \
    && pip install --no-cache-dir numpy openpyxl pytest "pyspark==3.5.3" pandas pyarrow

WORKDIR /workspace
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
