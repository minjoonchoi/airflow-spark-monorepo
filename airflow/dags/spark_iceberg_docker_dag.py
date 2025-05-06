"""
Docker를 활용하여 Spark 및 Iceberg 작업을 실행하는 Airflow DAG
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

from dags.tasks.spark_tasks import process_iceberg_table

# 기본 인수 정의
default_args = {
    'owner': 'data_engineer',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Airflow 홈 디렉토리 - 실제 환경에 맞게 수정 필요
AIRFLOW_HOME = '/Users/minjoon/workspace/airflow-spark-monorepo'  
WAREHOUSE_PATH = f'{AIRFLOW_HOME}/metastore/warehouse'
SPARK_PATH = f'{AIRFLOW_HOME}/spark'

# DAG 정의
dag = DAG(
    'spark_iceberg_docker_pipeline',
    default_args=default_args,
    description='Docker를 활용한 Spark와 Iceberg 데이터 파이프라인',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Docker 이미지 설정 (로컬에서 빌드 필요)
DOCKER_IMAGE = 'airflow-spark-monorepo:latest'

# PySpark & Iceberg 관련 환경 변수
SPARK_CONF = {
    "spark.driver.memory": "2g",
    "spark.executor.memory": "2g",
    "spark.executor.cores": "1",
    "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
    "spark.sql.catalog.spark_catalog.type": "hive",
    "spark.sql.catalog.local": "org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.local.type": "hadoop",
    "spark.sql.catalog.local.warehouse": "/mnt/warehouse",
    # Maven 패키지 경로 (이미 이미지에 포함되어 있음)
    "spark.jars": "/opt/spark/jars/iceberg-spark-runtime-2.12_3.4.1.jar"
}

# Docker 볼륨 마운트 설정
mounts = [
    # 웨어하우스 디렉토리 마운트
    Mount(
        source=WAREHOUSE_PATH,
        target='/mnt/warehouse',
        type='bind'
    ),
    # 로그 디렉토리 마운트 (선택)
    Mount(
        source=f'{AIRFLOW_HOME}/logs',
        target='/mnt/logs',
        type='bind'
    )
]

# 1. 데이터 추출 Docker 작업
extract_data = DockerOperator(
    task_id='extract_data',
    image=DOCKER_IMAGE,
    command='/app/extract_data.py --date {{ ds }}',
    docker_url='unix://var/run/docker.sock',
    mounts=mounts,
    auto_remove=True,
    environment={
        # Spark 설정을 환경 변수로 전달
        'SPARK_CONF': str(SPARK_CONF),
        'WAREHOUSE_PATH': '/mnt/warehouse',
    },
    dag=dag,
)

# 2. Iceberg 테이블 처리 작업 (Python Operator)
process_table = PythonOperator(
    task_id='process_iceberg_table',
    python_callable=process_iceberg_table,
    op_kwargs={
        'table_name': 'example_table',
        'warehouse_path': WAREHOUSE_PATH,
        'execution_date': '{{ ds }}'
    },
    dag=dag,
)

# 3. 데이터 분석 Docker 작업
analyze_data = DockerOperator(
    task_id='analyze_data',
    image=DOCKER_IMAGE,
    command='/app/analyze_data.py --table example_table --date {{ ds }}',
    docker_url='unix://var/run/docker.sock',
    mounts=mounts,
    auto_remove=True,
    environment={
        # Spark 설정을 환경 변수로 전달
        'SPARK_CONF': str(SPARK_CONF),
        'WAREHOUSE_PATH': '/mnt/warehouse',
    },
    dag=dag,
)

# 태스크 간 의존성 설정
extract_data >> process_table >> analyze_data 