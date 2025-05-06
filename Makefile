.PHONY: build-spark airflow-up airflow-down clean setup-dev run run-extract run-analyze spark-sql help iceberg-help

# Spark 이미지 빌드
build-spark:
	docker build -t airflow-spark-monorepo -f spark/Dockerfile .

# Airflow 환경 시작
airflow-up:
	cd airflow && docker-compose up -d

# Airflow 환경 중지
airflow-down:
	cd airflow && docker-compose down

# 전체 환경 중지 및 정리
clean: airflow-down
	docker rmi airflow-spark-monorepo

# 로컬 개발 환경 설정 (uv를 사용하여 venv 생성 및 의존성 설치)
setup-dev:
	pip install uv
	uv venv
	source .venv/bin/activate && \
	uv pip install -r airflow/requirements.txt && \
	uv pip install -r spark/requirements.txt

# 일반 Spark 스크립트 실행 함수 (안전하게 인수 처리)
# 사용법: make run SCRIPT=경로/스크립트.py ARGS="--인수1 값1 --인수2 값2"
run:
	@if [ -z "$(SCRIPT)" ]; then \
		echo "SCRIPT 변수가 필요합니다. 예: make run SCRIPT=extract_data.py ARGS=\"--date 2025-05-01\""; \
		exit 1; \
	fi
	@echo "실행: $(SCRIPT) $(ARGS)"
	@docker run --rm \
		-v $(PWD)/metastore:/app/metastore \
		airflow-spark-monorepo \
		"spark-submit $(SCRIPT) $(ARGS)"

# 데이터 추출 스크립트 실행
# 사용법: make extract DATE=2025-05-01
extract:
	@$(MAKE) run SCRIPT=extract_data.py ARGS="--date $(DATE)"

# 데이터 분석 스크립트 실행
# 사용법: make analyze INPUT=users OUTPUT=stats
analyze:
	@$(MAKE) run SCRIPT=analyze_data.py ARGS="--input_table $(INPUT) --output_table $(OUTPUT)"

# Ad-hoc SQL 쿼리 - 대화형 CLI 실행
spark-sql:
	docker run --rm -it \
		-v $(PWD)/metastore:/app/metastore \
		--name spark-sql-shell \
		airflow-spark-monorepo \
		"spark-sql"

# 도움말
help:
	@echo "사용 가능한 명령어:"
	@echo "  make build-spark  - Spark Docker 이미지 빌드"
	@echo "  make airflow-up   - Airflow 서비스 시작"
	@echo "  make airflow-down - Airflow 서비스 중지"
	@echo "  make clean        - 모든 리소스 정리"
	@echo "  make setup-dev    - 로컬 개발 환경 설정"
	@echo ""
	@echo "  ┌─────────────────────────────────────────────────────────────────┐"
	@echo "  │                       스크립트 실행 명령                        │"
	@echo "  ├─────────────────────────────────────────────────────────────────┤"
	@echo "  │ 데이터 추출 (extract_data.py):                                 │"
	@echo "  │  make extract DATE=2025-05-01                                  │"
	@echo "  │                                                                 │"
	@echo "  │ 데이터 분석 (analyze_data.py):                                 │"
	@echo "  │  make analyze INPUT=users OUTPUT=stats                         │"
	@echo "  │                                                                 │"
	@echo "  │ 임의의 스크립트 실행:                                          │"
	@echo "  │  make run SCRIPT=경로/스크립트.py ARGS=\"--인수1 값1 --인수2 값2\" │"
	@echo "  └─────────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "  make spark-sql    - Spark SQL 대화형 쉘 실행"
	@echo "  make iceberg-help - Iceberg 테이블 사용법 표시"
	@echo "  make help         - 이 도움말 표시"

# Iceberg 테이블 정보 및 사용법 표시
iceberg-help:
	@echo "\n===== Iceberg 테이블 사용법 ====="
	@echo "모든 카탈로그가 hadoop 타입으로 설정되어 있어 다음 두 가지 방법으로 테이블을 생성하고 사용할 수 있습니다:"
	@echo ""
	@echo "1. local 카탈로그 사용 (권장):"
	@echo "   CREATE TABLE local.my_table (id INT, name STRING) USING iceberg;"
	@echo "   INSERT INTO local.my_table VALUES (1, 'test');"
	@echo "   SELECT * FROM local.my_table;"
	@echo "   SHOW TABLES IN local;"
	@echo ""
	@echo "2. 기본 방식 (spark_catalog):"
	@echo "   CREATE TABLE my_table (id INT, name STRING) USING iceberg;"
	@echo "   INSERT INTO my_table VALUES (1, 'test');"
	@echo "   SELECT * FROM my_table;"
	@echo "   SHOW TABLES;"
	@echo ""
	@echo "두 방식 모두 컨테이너가 재시작되어도 테이블이 유지됩니다."
	@echo "USING iceberg 구문은 반드시 필요합니다."
	@echo ""
	@echo "===== 테이블 관리 명령어 ====="
	@echo "스키마 확인: DESCRIBE my_table;"
	@echo "히스토리 확인: SELECT * FROM my_table.history;"
	@echo "스냅샷 정보: SELECT * FROM my_table.snapshots;"
	@echo "파일 정보: SELECT * FROM my_table.files;"
	@echo "테이블 최적화: CALL system.rewrite_data_files(table => 'local.my_table');"
	@echo "==============================" 