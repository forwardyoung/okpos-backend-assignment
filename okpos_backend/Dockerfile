응# 1. 베이스 이미지 설정
FROM python:3.8-slim

# 2. 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. Poetry 설치
RUN pip install poetry

# 5. 의존성 파일 복사 및 설치
COPY poetry.lock pyproject.toml /app/
RUN poetry install --no-root --no-dev

# 6. 소스 코드 복사
COPY . /app/

# 7. Gunicorn 실행
# 포트 8000으로 Gunicorn 서버를 실행합니다.
CMD ["poetry", "run", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
