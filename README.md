# FHE-based Privacy-Preserving Recommender System

## 프로젝트 개요

Microsoft SEAL 라이브러리의 CKKS 동형암호 스킴을 활용하여 사용자 프라이버시를 보호하면서 맞춤형 추천을 제공하는 시스템입니다.

## 주요 기능

- ✅ CKKS 동형암호를 이용한 사용자 선호도 벡터 암호화
- ✅ 암호화 상태에서의 내적 연산 및 유사도 계산
- ✅ 임계값 기반 필터링 및 Top-K 추천
- ✅ MovieLens 1M 데이터셋 기반 실험

## 기술 스택

- **동형암호**: Microsoft SEAL (TenSEAL)
- **암호화 스킴**: CKKS
- **데이터셋**: MovieLens 1M (6,040 users, 3,706 movies)
- **언어**: Python 3.10+
- **환경**: AWS EC2 (g6e.xlarge)

## 프로젝트 구조

fhe-recommender/
├── data/ # 데이터셋
│ ├── raw/ # 원본 데이터
│ ├── processed/ # 전처리 데이터
│ └── encrypted/ # 암호화 데이터
├── keys/ # CKKS 키 (비밀키/공개키)
├── src/
│ ├── client/ # 클라이언트 (암호화/복호화)
│ ├── server/ # 서버 (동형 연산)
│ └── utils/ # 유틸리티
├── results/ # 실험 결과
├── logs/ # 로그
└── notebooks/ # Jupyter 노트북

text

## 설치 및 실행

### 환경 설정

가상환경 생성
python3 -m venv venv
source venv/bin/activate

의존성 설치
pip install -r requirements.txt

text

### 데이터 준비

MovieLens 1M 다운로드
cd data/raw
wget https://files.grouplens.org/datasets/movielens/ml-1m.zip
unzip ml-1m.zip
cd ../..

text

### 파이프라인 실행

1. 데이터 전처리
python src/utils/data_prep.py

2. CKKS 키 생성
python src/utils/keygen.py

3. 사용자 벡터 암호화
python src/client/encrypt.py

4. 서버 동형 연산
python src/server/evaluator.py

5. 복호화 및 추천
python src/client/decrypt.py

전체 파이프라인 자동 실행
./run_pipeline.sh

text

### 배치 처리 (전체 사용자)

10명 테스트
python batch_process_all_users.py --num-users 10

전체 사용자 처리
python batch_process_all_users.py

text

## 실험 결과

- **키 생성 시간**: ~5초
- **암호화 시간**: ~3초/사용자
- **동형 내적 연산**: ~15초/사용자 (512개 아이템)
- **복호화 시간**: ~2초/사용자

자세한 결과는 `results/` 디렉토리 참조

## 참고 문헌

- Microsoft SEAL: https://github.com/microsoft/SEAL
- TenSEAL: https://github.com/OpenMined/TenSEAL
- MovieLens: https://grouplens.org/datasets/movielens/

## 라이선스

MIT License

## 저자

[Your Name] - [University Name]

동형암호(FHE) 활용 개별연구 프로젝트
