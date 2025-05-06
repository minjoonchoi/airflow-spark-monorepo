"""
Spark 및 Iceberg를 사용하는 샘플 Airflow DAG
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

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

# DAG 정의
dag = DAG(
    'spark_iceberg_pipeline',
    default_args=default_args,
    description='Spark와 Iceberg를 사용한 데이터 파이프라인',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# Spark 작업 설정
spark_conf = {
    "spark.driver.memory": "2g",
    "spark.executor.memory": "2g",
    "spark.executor.cores": "1",
    "spark.sql.extensions": "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
    "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
    "spark.sql.catalog.spark_catalog.type": "hive",
    "spark.sql.catalog.local": "org.apache.iceberg.spark.SparkCatalog",
    "spark.sql.catalog.local.type": "hadoop",
    "spark.sql.catalog.local.warehouse": "${AIRFLOW_HOME}/metastore/warehouse",
}

# 1. 데이터 추출 Spark 작업
extract_data = SparkSubmitOperator(
    task_id='extract_data',
    application='${AIRFLOW_HOME}/spark/extract_data.py',
    conn_id='spark_default',
    application_args=['--date', '{{ ds }}'],
    conf=spark_conf,
    dag=dag,
)

# 2. Iceberg 테이블 처리 작업
process_table = PythonOperator(
    task_id='process_iceberg_table',
    python_callable=process_iceberg_table,
    op_kwargs={
        'table_name': 'example_table',
        'warehouse_path': '${AIRFLOW_HOME}/metastore/warehouse',
        'execution_date': '{{ ds }}'
    },
    dag=dag,
)

# 3. 최종 분석 Spark 작업
analyze_data = SparkSubmitOperator(
    task_id='analyze_data',
    application='${AIRFLOW_HOME}/spark/analyze_data.py',
    conn_id='spark_default',
    application_args=['--table', 'example_table', '--date', '{{ ds }}'],
    conf=spark_conf,
    dag=dag,
)

# 태스크 간 의존성 설정
extract_data >> process_table >> analyze_data 