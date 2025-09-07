# 1. 베이스 이미지
FROM python:3.8-slim

# 2. 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. 작업 디렉토리
WORKDIR /app

# 4. 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc build-essential libgl1 libglib2.0-0 curl \
    && rm -rf /var/lib/apt/lists/*

# 5. pip 업그레이드
RUN pip install --upgrade pip

# 6. requirements.txt 복사 및 설치
COPY ../requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 7. 소스 코드 복사
COPY .. /app/

# 8. Gunicorn 실행
ENTRYPOINT ["/app/docker/entrypoint.sh"]
