import os
import sys
import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import normalize
import yaml
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from logger import setup_logger, log_exception

logger = setup_logger('data_prep', level=logging.DEBUG)

def load_config():
    try:
        logger.info("설정 파일 로드 중...")
        with open('config/params.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.info("설정 파일 로드 완료")
        return config
    except Exception as e:
        log_exception(logger, e, "load_config")
        raise

def load_movielens_1m():
    """MovieLens 1M 데이터 로드"""
    try:
        logger.info("MovieLens 1M 데이터셋 로드 시작")
        config = load_config()
        data_path = config['dataset']['path']
        
        ratings_file = os.path.join(data_path, 'ratings.dat')
        logger.debug(f"파일 경로: {ratings_file}")
        
        if not os.path.exists(ratings_file):
            logger.error(f"파일이 존재하지 않음: {ratings_file}")
            raise FileNotFoundError(f"ratings.dat not found at {ratings_file}")
        
        logger.info("ratings.dat 파싱 중...")
        ratings = pd.read_csv(
            ratings_file,
            sep='::',
            engine='python',
            names=['userId', 'movieId', 'rating', 'timestamp']
        )
        
        logger.info(f"데이터 로드 완료:")
        logger.info(f"  - 총 평점 수: {len(ratings):,}")
        logger.info(f"  - 사용자 수: {ratings['userId'].nunique():,}")
        logger.info(f"  - 영화 수: {ratings['movieId'].nunique():,}")
        logger.info(f"  - 평점 범위: {ratings['rating'].min()} - {ratings['rating'].max()}")
        
        return ratings
        
    except Exception as e:
        log_exception(logger, e, "load_movielens_1m")
        raise

def create_user_item_matrix(ratings, min_rating=3.0):
    """User-Item 행렬 생성"""
    try:
        logger.info(f"User-Item 행렬 생성 시작 (최소 평점: {min_rating})")
        
        original_count = len(ratings)
        ratings_filtered = ratings[ratings['rating'] >= min_rating].copy()
        filtered_count = len(ratings_filtered)
        
        logger.info(f"필터링: {original_count:,} -> {filtered_count:,} ({filtered_count/original_count*100:.1f}%)")
        
        ratings_filtered['rating'] = 1.0
        
        logger.info("Pivot table 생성 중...")
        user_item = ratings_filtered.pivot_table(
            index='userId',
            columns='movieId',
            values='rating',
            fill_value=0
        )
        
        logger.info(f"User-Item 행렬 shape: {user_item.shape}")
        logger.info(f"Sparsity: {(user_item == 0).sum().sum() / (user_item.shape[0] * user_item.shape[1]) * 100:.2f}%")
        
        return user_item
        
    except Exception as e:
        log_exception(logger, e, "create_user_item_matrix")
        raise

def vectorize_and_normalize(user_item_matrix, max_dim=512):
    """벡터화 및 정규화 - 올바른 버전"""
    try:
        logger.info(f"벡터 차원 축소 및 정규화 시작 (목표 차원: {max_dim})")
        
        # 차원 축소: 상위 인기 영화 선택
        item_counts = user_item_matrix.sum(axis=0).sort_values(ascending=False)
        top_items = item_counts.head(max_dim).index
        
        logger.info(f"상위 {max_dim}개 인기 영화 선택")
        logger.info(f"선택된 영화의 평균 평점 수: {item_counts.head(max_dim).mean():.1f}")
        
        # 선택된 영화로 축소
        user_item_reduced = user_item_matrix[top_items]
        
        logger.info(f"축소된 User-Item 행렬 shape: {user_item_reduced.shape}")
        logger.info(f"  → {user_item_reduced.shape[0]}명 사용자 × {user_item_reduced.shape[1]}개 영화")
        
        # 정규화
        logger.info("L2 정규화 수행 중...")
        
        # 사용자 벡터: 각 사용자의 영화 선호도 (행 단위 정규화)
        # shape: (num_users, max_dim)
        user_vectors = normalize(user_item_reduced.values, axis=1)
        
        # 아이템 벡터: 각 영화에 대한 사용자 반응 패턴을 영화 특성으로 변환
        # 전치 후 다시 max_dim 차원으로 축소
        item_matrix_T = user_item_reduced.T  # (max_dim, num_users)
        
        # 아이템도 사용자와 같은 차원(max_dim)으로 맞추기 위해
        # 사용자 중 상위 max_dim명 선택 또는 차원 축소
        # 여기서는 간단히: 아이템 벡터 = 전치된 행렬의 각 행 (영화별 사용자 평점 패턴)
        
        # 방법 1: 아이템 벡터를 사용자 벡터와 동일한 공간으로 투영
        # 가장 간단한 방법: 아이템 행렬을 전치하지 않고, 같은 영화 차원 사용
        item_vectors = user_vectors[:max_dim].copy()  # 상위 max_dim명 사용자를 아이템 대표로
        
        # 방법 2 (더 정확): 아이템을 max_dim 차원의 임베딩으로 표현
        # SVD 등으로 차원 축소 가능하지만, 여기서는 단순화
        # 실제로는: 각 아이템의 특성을 max_dim 차원으로 인코딩
        
        # 수정된 방법: 각 아이템을 max_dim 차원 벡터로 표현
        # user_item_reduced는 이미 (num_users, max_dim)
        # item 벡터는 이 행렬을 전치한 후, 각 아이템(영화)의 벡터를 추출
        # 하지만 차원을 맞추려면, 아이템도 max_dim 차원이어야 함
        
        # 최종 방법: 아이템 벡터 = 전치 행렬에서 상위 사용자 패턴 기반 축소
        from sklearn.decomposition import TruncatedSVD
        
        logger.info("아이템 벡터 차원 축소 (SVD) 수행 중...")
        svd = TruncatedSVD(n_components=max_dim, random_state=42)
        item_features = svd.fit_transform(user_item_reduced.T.values)  # (max_dim, max_dim)
        
        # 정규화
        item_vectors = normalize(item_features, axis=1)
        
        logger.info(f"사용자 벡터 shape: {user_vectors.shape}")
        logger.info(f"아이템 벡터 shape: {item_vectors.shape}")
        logger.info(f"  → 사용자: {user_vectors.shape[0]}명 × {user_vectors.shape[1]}차원")
        logger.info(f"  → 아이템: {item_vectors.shape[0]}개 × {item_vectors.shape[1]}차원")
        
        # 차원 일치 확인
        assert user_vectors.shape[1] == item_vectors.shape[1], \
            f"차원 불일치: user({user_vectors.shape[1]}) vs item({item_vectors.shape[1]})"
        
        logger.info("✓ 내적 연산을 위한 차원 일치 확인 완료")
        logger.info(f"벡터 메모리 사용량: {(user_vectors.nbytes + item_vectors.nbytes) / 1024 / 1024:.2f} MB")
        
        return user_vectors, item_vectors, top_items.tolist()
        
    except Exception as e:
        log_exception(logger, e, "vectorize_and_normalize")
        raise

def save_processed_data(user_vectors, item_vectors, item_ids):
    """전처리 데이터 저장"""
    try:
        logger.info("전처리 데이터 저장 시작")
        
        output_dir = Path('data/processed')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        files = {
            'user_vectors.npy': user_vectors,
            'item_vectors.npy': item_vectors,
            'item_ids.npy': item_ids
        }
        
        for filename, data in files.items():
            filepath = output_dir / filename
            np.save(filepath, data)
            logger.info(f"저장 완료: {filepath} ({os.path.getsize(filepath) / 1024:.1f} KB)")
        
        logger.info("전처리 데이터 저장 완료")
        
    except Exception as e:
        log_exception(logger, e, "save_processed_data")
        raise

if __name__ == '__main__':
    try:
        logger.info("=" * 60)
        logger.info("MovieLens 데이터 전처리 시작")
        logger.info("=" * 60)
        
        ratings = load_movielens_1m()
        user_item = create_user_item_matrix(ratings)
        user_vectors, item_vectors, item_ids = vectorize_and_normalize(user_item)
        save_processed_data(user_vectors, item_vectors, item_ids)
        
        logger.info("=" * 60)
        logger.info("전처리 완료!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.critical("전처리 실패!")
        log_exception(logger, e, "main")
        sys.exit(1)
