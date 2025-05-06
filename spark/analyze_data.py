#!/usr/bin/env python
"""
Iceberg 테이블 데이터 분석을 위한 PySpark 스크립트 (Docker 환경에서 실행)
"""
import argparse
import ast
import logging
import os
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import sum, avg, count, col

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """명령줄 인수 파싱"""
    parser = argparse.ArgumentParser(description='데이터 분석 스크립트')
    parser.add_argument('--table', type=str, required=True, help='분석할 Iceberg 테이블 이름')
    parser.add_argument('--date', type=str, required=True, help='분석할 날짜 (YYYY-MM-DD)')
    return parser.parse_args()

def create_spark_session():
    """
    Spark 세션 생성
    환경 변수에서 설정을 가져오거나 기본값 사용
    """
    builder = SparkSession.builder.appName("Analyze Data Job")
    
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

def analyze_data(spark, table_name, date_str):
    """
    Iceberg 테이블 데이터 분석 및 결과 저장
    
    Args:
        spark: Spark 세션
        table_name: 분석할 Iceberg 테이블 이름
        date_str: 분석할 날짜 문자열 (YYYY-MM-DD)
    """
    logger.info(f"Analyzing data for table: {table_name}, date: {date_str}")
    
    # Docker 환경에서는 웨어하우스 경로가 /mnt/warehouse로 마운트됨
    logger.info("Spark 카탈로그 설정 확인")
    for catalog in spark.conf.get("spark.sql.catalog.iceberg.warehouse", ""), spark.conf.get("spark.sql.warehouse.dir", ""):
        logger.info(f"웨어하우스 경로: {catalog}")
    
    # 전체 테이블 이름 구성
    full_table_name = f"iceberg.db.{table_name}"
    
    # 데이터 읽기
    try:
        df = spark.table(full_table_name).filter(col("date") == date_str)
        
        if df.rdd.isEmpty():
            logger.warning(f"테이블 {full_table_name}에 {date_str} 날짜의 데이터가 없습니다.")
            return
        
        # 기본 통계 계산
        stats = df.agg(
            count("id").alias("count"),
            sum("value").alias("total_value"),
            avg("value").alias("avg_value")
        ).collect()[0]
        
        logger.info(f"분석 결과: 레코드 수={stats['count']}, 총합={stats['total_value']}, 평균={stats['avg_value']}")
        
        # 분석 결과를 별도 테이블에 저장
        result_df = spark.createDataFrame([{
            "date": date_str,
            "record_count": stats["count"],
            "total_value": float(stats["total_value"]),
            "avg_value": float(stats["avg_value"]),
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        # 분석 결과 테이블에 저장
        analysis_table = "iceberg.db.example_table_analysis"
        result_df.writeTo(analysis_table) \
            .tableProperty("format-version", "2") \
            .partitionedBy("date") \
            .createOrReplace()
        
        logger.info(f"분석 결과가 {analysis_table} 테이블에 저장되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터 분석 중 오류 발생: {e}")
        raise

def main():
    """메인 함수"""
    args = parse_args()
    table_name = args.table
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
        analyze_data(spark, table_name, date_str)
        logger.info("데이터 분석 작업 완료")
        return 0
    except Exception as e:
        logger.error(f"데이터 분석 중 오류 발생: {e}")
        return 1
    finally:
        spark.stop()

if __name__ == "__main__":
    exit(main()) 