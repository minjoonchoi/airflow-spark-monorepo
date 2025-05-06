"""
예제 DAG 파일: 기본적인 Airflow 파이프라인을 정의합니다.
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

# 기본 인수 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG 정의
dag = DAG(
    'example_dag',
    default_args=default_args,
    description='간단한 예제 DAG',
    schedule_interval=timedelta(days=1),
    catchup=False,
)

# 간단한 Python 함수 정의
def print_hello():
    return "Hello, Airflow!"

# 태스크 정의
hello_task = PythonOperator(
    task_id='hello_task',
    python_callable=print_hello,
    dag=dag,
)

bash_task = BashOperator(
    task_id='bash_task',
    bash_command='echo "현재 시간: $(date)"',
    dag=dag,
)

# 태스크 간 의존성 설정
hello_task >> bash_task 