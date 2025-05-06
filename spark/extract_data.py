#!/usr/bin/env python
"""
데이터 추출을 위한 PySpark 스크립트 (Docker 환경에서 실행)
"""
import argparse
import ast
import logging
import os
from datetime import datetime

from pyspark.sql import SparkSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='데이터 추출 스크립트')
    parser.add_argument('--date', type=str, required=True, help='처리할 날짜 (YYYY-MM-DD)')
    return parser.parse_args()

def create_spark_session():
    """
    Spark 세션 생성
    환경 변수에서 설정을 가져오거나 기본값 사용
    """
    builder = SparkSession.builder.appName("Extract Data Job")
    
    # Docker 환경에서 전달된 설정이 있으면 적용
    spark_conf_str = os.environ.get('SPARK_CONF')
    if spark_conf_str:
        try:
            spark_conf = ast.literal_eval(spark_conf_str)
            for key, value in spark_conf.items():
                builder = builder.config(key, value)
            logger.info("Docker 환경에서 전달된 Spark 설정 적용")
        except Exception as e:
            logger.warning(f"Spark 설정 파싱 오류: {e}")
    
    # Hive 지원 활성화
    builder = builder.enableHiveSupport()
    
    return builder.getOrCreate()

def extract_data(spark, date_str):
    """
    소스 데이터를 추출하여 Iceberg 테이블에 저장
    
    Args:
        spark: Spark 세션
        date_str: 처리할 날짜 문자열 (YYYY-MM-DD)
    """
    logger.info(f"Extracting data for date: {date_str}")
    
    # 예시 데이터 생성 (실제로는 외부 소스에서 데이터를 가져올 것)
    data = [
        (1, "Product A", 100.0, date_str),
        (2, "Product B", 200.0, date_str),
        (3, "Product C", 300.0, date_str),
        (4, "Product D", 400.0, date_str),
        (5, "Product E", 500.0, date_str),
    ]
    
    columns = ["id", "name", "value", "date"]
    df = spark.createDataFrame(data, columns)
    
    # Docker 환경에서는 웨어하우스 경로가 /mnt/warehouse로 마운트되어 있어야 함
    logger.info("Spark 카탈로그 설정 확인")
    for catalog in spark.conf.get("spark.sql.catalog.iceberg.warehouse", ""), spark.conf.get("spark.sql.warehouse.dir", ""):
        logger.info(f"웨어하우스 경로: {catalog}")
    
    # Iceberg 테이블에 데이터 쓰기
    table_name = "iceberg.db.example_table"
    
    # 테이블이 없는 경우 생성
    try:
        df.writeTo(table_name) \
          .tableProperty("format-version", "2") \
          .partitionedBy("date") \
          .createOrReplace()
        logger.info(f"Created or replaced table: {table_name}")
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        # 이미 테이블이 존재하는 경우 추가
        try:
            df.writeTo(table_name) \
              .append()
            logger.info(f"Appended data to table: {table_name}")
        except Exception as e:
            logger.error(f"Error appending to table: {e}")
            raise

def main():
    """메인 함수"""
    args = parse_args()
    date_str = args.date
    
    try:
        # 날짜 형식 검증
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logger.error(f"잘못된 날짜 형식: {date_str}. 'YYYY-MM-DD' 형식이어야 합니다.")
        return 1
    
    # Docker 환경 로그
    logger.info("Docker 컨테이너에서 실행 중")
    logger.info(f"웨어하우스 경로: {os.environ.get('WAREHOUSE_PATH', '환경 변수 없음')}")
    
    spark = create_spark_session()
    try:
        extract_data(spark, date_str)
        logger.info("데이터 추출 작업 완료")
        return 0
    except Exception as e:
        logger.error(f"데이터 추출 중 오류 발생: {e}")
        return 1
    finally:
        spark.stop()

if __name__ == "__main__":
    exit(main()) 