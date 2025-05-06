# Airflow Spark 모노레포 프로젝트

이 프로젝트는 **모노레포(Monorepo)** 아키텍처를 활용하여 데이터 파이프라인의 두 가지 핵심 구성 요소인 **워크플로우 오케스트레이션(Airflow)**과 **데이터 처리 로직(Spark)**을 단일 레포지토리에서 관리합니다. PySpark와 Apache Iceberg를 활용한 확장 가능한 데이터 처리 환경을 제공합니다.

## 모노레포 아키텍처 개요

모노레포는 여러 개의 관련 프로젝트를 하나의 통합된 코드 저장소에서 관리하는 개발 방식입니다. 이 프로젝트에서는 다음과 같은 이점을 제공합니다:

1. **통합된 버전 관리**: Airflow DAG와 Spark 작업의 버전을 동시에 관리하여 일관성 유지
2. **간소화된 의존성 관리**: 각 구성 요소가 자체 의존성을 독립적으로 관리하면서도 통합 개발 환경 유지
3. **원활한 협업**: 데이터 엔지니어링 팀이 전체 파이프라인 코드에 쉽게 접근
4. **빠른 반복 개발**: 변경 사항을 빠르게 테스트하고 배포 가능

## 프로젝트 구성 요소

### 1. Airflow (워크플로우 오케스트레이션)

`airflow/` 디렉토리에 위치한 이 구성 요소는 전체 데이터 파이프라인의 스케줄링, 모니터링 및 오케스트레이션을 담당합니다:

- **DAG 정의**: 파이프라인 워크플로우 정의
- **작업 스케줄링**: 시간 기반 또는 트리거 기반 실행
- **모니터링 및 알림**: 파이프라인 상태 추적 및 문제 알림
- **에러 처리 및 재시도**: 오류 발생 시 복구 메커니즘

### 2. Spark (데이터 처리 로직)

`spark/` 디렉토리에 위치한 이 구성 요소는 실제 데이터 처리 로직을 포함합니다:

- **데이터 추출**: 외부 소스에서 데이터 수집
- **데이터 변환**: 비즈니스 로직에 따른 데이터 처리
- **데이터 적재**: Apache Iceberg 테이블에 데이터 저장
- **분석 작업**: 데이터 집계 및 인사이트 도출

### 3. Metastore (데이터 저장소)

`metastore/` 디렉토리는 Iceberg 테이블의 메타데이터와 실제 데이터를 저장하는 공간입니다:

- **메타데이터 관리**: 테이블 스키마, 파티션 정보 등 저장
- **데이터 웨어하우스**: 실제 데이터 파일 저장
- **공유 저장소**: Airflow와 Spark 간에 공유되는 중앙 저장소

## 디렉토리 구조

```
airflow-spark-monorepo/
├── airflow/                   # Airflow 관련 모든 파일
│   ├── dags/                  # DAG 정의 파일
│   │   ├── spark_iceberg_dag.py      # SparkSubmitOperator 사용 DAG
│   │   └── spark_iceberg_docker_dag.py # DockerOperator 사용 DAG
│   ├── plugins/               # 커스텀 Airflow 플러그인
│   ├── config/                # Airflow 설정 파일
│   ├── logs/                  # Airflow 로그 파일
│   ├── docker-compose.yml     # Airflow 환경 Docker Compose 설정
│   └── requirements.txt       # Airflow 환경 의존성 파일
├── spark/                     # Spark 작업 스크립트
│   ├── extract_data.py        # 데이터 추출 스크립트
│   ├── analyze_data.py        # 데이터 분석 스크립트
│   ├── requirements.txt       # Spark 작업 의존성 파일
│   └── Dockerfile             # Spark 작업용 Docker 이미지 구성
├── metastore/                 # 메타데이터 및 Iceberg 웨어하우스
│   └── warehouse/             # 테이블 데이터 저장소
├── Makefile                   # 프로젝트 관리 명령어 모음
└── README.md                  # 프로젝트 문서
```

## Spark 환경 구성 (Dockerfile)

프로젝트는 빠른 개발과 테스트를 위해 `bitnami/spark:3.4.1` 이미지 기반의 Docker 컨테이너를 사용합니다:

```dockerfile
FROM bitnami/spark:3.4.1

USER root

# 추가 시스템 패키지 설치
RUN apt-get update && apt-get install -y curl python3-pip && rm -rf /var/lib/apt/lists/*

# Iceberg JAR 다운로드
ENV ICEBERG_VERSION=1.3.1
RUN curl -L -o /opt/bitnami/spark/jars/iceberg-spark-runtime-3.4_2.12-${ICEBERG_VERSION}.jar \
    https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.4_2.12/${ICEBERG_VERSION}/iceberg-spark-runtime-3.4_2.12-${ICEBERG_VERSION}.jar

# PySpark 스크립트 및 의존성 설치
COPY spark/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 스크립트 복사 및 실행 권한 부여
COPY spark/*.py /app/
RUN chmod +x /app/*.py

# spark-submit을 기본 엔트리포인트로 설정
ENTRYPOINT ["spark-submit", "--jars", "/opt/bitnami/spark/jars/iceberg-spark-runtime-3.4_2.12-1.3.1.jar"]
```

## 설치 및 시작하기

### 전체 환경 설정 (처음 시작하는 경우)

```bash
# 1. 프로젝트 클론
git clone https://github.com/your-username/airflow-spark-monorepo.git
cd airflow-spark-monorepo

# 2. 디렉토리 구조 확인
ls -la

# 3. Spark 이미지 빌드
make build-spark

# 4. Airflow 환경 시작
make airflow-up

# 5. 브라우저에서 Airflow UI 접속
# http://localhost:8080 (기본 계정: airflow/airflow)
```

### Airflow 환경만 시작하기 (이미 설정이 완료된 경우)

```bash
# Airflow 서비스 시작
make airflow-up

# 브라우저에서 Airflow UI 확인
# http://localhost:8080
```

## 개발 환경 설정

로컬에서 개발 및 테스트를 위한 환경 설정:

```bash
# 가상 환경 및 의존성 설치 (uv 사용)
make setup-dev

# 가상 환경 활성화
source .venv/bin/activate
```

## Spark 작업 실행하기

### 1. 범용 실행 명령 (모든 스크립트)

```bash
# 임의의 Spark 스크립트를 실행하는 범용 명령
make run SCRIPT=extract_data.py ARGS="--date 2025-05-01"
make run SCRIPT=custom_job.py ARGS="--param1 value1 --param2 value2"
```

### 2. 특정 작업 실행 명령 (래퍼)

```bash
# 데이터 추출 작업 실행
make run-extract ARGS="--date 2025-05-01"

# 데이터 분석 작업 실행
make run-analyze ARGS="--input_table users --output_table user_stats"
```

### 3. 대화형 Spark SQL 쉘

```bash
# Iceberg 테이블에 대한 SQL 쿼리 실행을 위한 대화형 쉘
make spark-sql
```

## Iceberg 테이블 작업

Apache Iceberg를 사용하여 메타데이터 및 스키마 관리하는 방법 확인:

```bash
# Iceberg 테이블 사용법 및 관리 명령어 확인
make iceberg-help
```

### 예시 테이블 생성 및 사용

```sql
-- 테이블 생성
CREATE TABLE iceberg.db.example_table (
    id BIGINT,
    name STRING,
    value DOUBLE,
    created_at TIMESTAMP
)
USING iceberg
PARTITIONED BY (days(created_at));

-- 데이터 삽입
INSERT INTO iceberg.db.example_table VALUES
    (1, 'name1', 10.5, current_timestamp()),
    (2, 'name2', 20.5, current_timestamp());

-- 데이터 조회
SELECT * FROM iceberg.db.example_table;

-- 스냅샷 및 히스토리 확인
SELECT * FROM iceberg.db.example_table.history;
```

## Airflow에서 Spark 작업 실행

### DockerOperator 사용 (권장)

```python
extract_task = DockerOperator(
    task_id='extract_data',
    image='airflow-spark-monorepo:latest',
    command='extract_data.py --date {{ ds }}',
    docker_url='unix://var/run/docker.sock',
    mounts=[
        Mount(source='/path/to/metastore', target='/app/metastore', type='bind')
    ],
    environment={},
)
```

### 전체 명령어 목록 확인

```bash
# 사용 가능한 모든 명령어 확인
make help
```

## 의존성 관리

이 모노레포는 각 구성 요소의 의존성을 명확하게 분리하여 관리합니다:

```bash
# Airflow 의존성 설치
pip install -r airflow/requirements.txt

# Spark 의존성 설치
pip install -r spark/requirements.txt

# 또는 모든 의존성 한번에 설치
make setup-dev
```

## 깨끗하게 정리하기

```bash
# Airflow 서비스 중지
make airflow-down

# 모든 리소스 정리 (Docker 이미지 포함)
make clean
```