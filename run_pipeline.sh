#!/bin/bash
set -e

echo "======================================"
echo "FHE 추천 시스템 파이프라인 실행"
echo "======================================"

# 가상환경 활성화
source venv/bin/activate

# 1. 데이터 전처리
echo "[1/5] 데이터 전처리..."
python src/utils/data_prep.py

# 2. 키 생성
echo "[2/5] CKKS 키 생성..."
python src/utils/keygen.py

# 3. 클라이언트 암호화
echo "[3/5] 사용자 벡터 암호화..."
python src/client/encrypt.py

# 4. 서버 연산
echo "[4/5] 서버 동형 연산..."
python src/server/evaluator.py

# 5. 복호화 및 추천
echo "[5/5] 결과 복호화 및 Top-K 추천..."
python src/client/decrypt.py

echo "======================================"
echo "파이프라인 실행 완료!"
echo "======================================"
