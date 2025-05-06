FROM bitnami/spark:3.4.1

USER root

# 추가 시스템 패키지 설치 (필요한 경우)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# Metastore 디렉토리 생성
RUN mkdir -p /app/metastore/warehouse && \
    chmod -R 777 /app/metastore

# Iceberg JAR 다운로드 (이미 bitnami 이미지에 포함되어 있을 수 있으나, 최신 버전 보장을 위해)
ENV ICEBERG_VERSION=1.3.1
RUN curl -L -o /opt/bitnami/spark/jars/iceberg-spark-runtime-3.4_2.12-${ICEBERG_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.4_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.4_2.12-${ICEBERG_VERSION}.jar

# Spark 기본 설정 추가 (Makefile에서 옮겨옴)
RUN echo "spark.sql.extensions org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions" > /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.defaultCatalog iceberg" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.iceberg org.apache.iceberg.spark.SparkCatalog" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.iceberg.type hadoop" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.iceberg.warehouse /app/metastore/warehouse" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.spark_catalog org.apache.iceberg.spark.SparkCatalog" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.spark_catalog.type hadoop" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.sql.catalog.spark_catalog.warehouse /app/metastore/warehouse" >> /opt/bitnami/spark/conf/spark-defaults.conf && \
    echo "spark.jars /opt/bitnami/spark/jars/iceberg-spark-runtime-3.4_2.12-1.3.1.jar" >> /opt/bitnami/spark/conf/spark-defaults.conf

# Python 요구사항 복사 및 설치
COPY spark/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Python 스크립트 복사
COPY spark/*.py /app/

# 실행 권한 부여
RUN chmod +x /app/*.py

# 환경 변수 설정
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

# PATH 설정 (모든 Spark 명령어에 접근 가능하도록)
ENV PATH="/opt/bitnami/spark/bin:${PATH}"

# 기본 쉘 엔트리포인트 설정 (유연성 향상)
ENTRYPOINT ["/bin/bash", "-c"]

# 기본 명령은 비워두고, 명령줄에서 직접 지정
CMD [""] 