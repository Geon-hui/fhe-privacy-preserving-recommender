import sys
import time
import numpy as np
import tenseal as ts
import yaml
from pathlib import Path
from tqdm import tqdm

sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from logger import setup_logger, log_exception
from report_generator import ExperimentReporter

logger = setup_logger('evaluator')

def load_public_context():
    """공개키 컨텍스트 로드"""
    try:
        context_path = Path('keys/public_context.bin')
        logger.info(f"공개키 컨텍스트 로드: {context_path}")
        
        if not context_path.exists():
            raise FileNotFoundError(f"공개키 파일이 없습니다: {context_path}")
        
        with open(context_path, 'rb') as f:
            context = ts.context_from(f.read())
        
        logger.info("공개키 컨텍스트 로드 완료")
        return context
        
    except Exception as e:
        log_exception(logger, e, "load_public_context")
        raise

def load_config():
    try:
        with open('config/params.yaml', 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        log_exception(logger, e, "load_config")
        raise

def compute_encrypted_recommendations(user_id=0):
    """암호화 상태에서 추천 연산 with 결과 기록"""
    reporter = ExperimentReporter('server_evaluation')
    
    try:
        logger.info("=" * 60)
        logger.info(f"사용자 {user_id} 추천 연산 시작 (서버)")
        logger.info("=" * 60)
        
        context = load_public_context()
        config = load_config()['recommendation']
        
        # 암호화된 사용자 벡터 로드
        encrypted_path = Path(f'data/encrypted/user_{user_id}.bin')
        logger.info(f"암호화된 사용자 벡터 로드: {encrypted_path}")
        
        if not encrypted_path.exists():
            raise FileNotFoundError(f"암호화된 사용자 파일이 없습니다: {encrypted_path}")
        
        with open(encrypted_path, 'rb') as f:
            encrypted_user = ts.ckks_vector_from(context, f.read())
        
        logger.info("암호화된 사용자 벡터 로드 완료")
        
        # 아이템 벡터 로드
        item_vectors_path = Path('data/processed/item_vectors.npy')
        logger.info(f"아이템 벡터 로드: {item_vectors_path}")
        item_vectors = np.load(item_vectors_path)
        
        logger.info(f"아이템 벡터 shape: {item_vectors.shape}")
        
        # Shape 확인 및 수정
        # item_vectors는 (512, 6039) 형태 → 각 아이템은 6039차원
        # 하지만 사용자 벡터는 512차원이므로, 아이템 벡터를 전치해야 함
        # 실제로는: 각 아이템을 512차원으로 표현해야 함
        
        # 수정: 아이템 벡터를 행 기준으로 읽어야 함 (각 행이 하나의 아이템)
        num_items = item_vectors.shape[0]
        item_dim = item_vectors.shape[1]
        
        logger.info(f"아이템 수: {num_items}, 아이템 차원: {item_dim}")
        logger.info(f"총 {num_items}개 아이템과 내적 연산 수행 중...")
        
        # 내적 연산 (암호화 상태)
        encrypted_scores = []
        computation_times = []
        
        start_total = time.time()
        
        for idx in tqdm(range(num_items), desc="동형 내적 연산"):
            item_vec = item_vectors[idx]
            
            # 연산 시간 측정
            start_time = time.time()
            
            try:
                # 내적 연산: encrypted_user · item_vec
                score = encrypted_user.dot(item_vec.tolist())
                encrypted_scores.append(score)
                
                comp_time = time.time() - start_time
                computation_times.append(comp_time)
                
            except Exception as e:
                logger.error(f"아이템 {idx} 연산 실패: {str(e)}")
                logger.error(f"사용자 벡터 차원 vs 아이템 벡터 차원: ? vs {len(item_vec)}")
                raise
        
        total_time = time.time() - start_total
        avg_time = np.mean(computation_times)
        
        logger.info(f"총 {len(encrypted_scores)}개 암호화된 점수 생성")
        logger.info(f"총 연산 시간: {total_time:.2f}초")
        logger.info(f"평균 연산 시간: {avg_time:.4f}초/아이템")
        logger.info(f"처리량: {num_items / total_time:.2f} 아이템/초")
        
        # 암호화된 점수 저장
        output_path = Path(f'data/encrypted/scores_user_{user_id}.npy')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"암호화된 점수 저장 중: {output_path}")
        
        import pickle
        with open(output_path, 'wb') as f:
            pickle.dump([s.serialize() for s in encrypted_scores], f)
        
        file_size = output_path.stat().st_size
        logger.info(f"저장 완료: {output_path} ({file_size / 1024:.1f} KB)")
        
        # 결과 기록
        reporter.add_stage(
            'Encrypted Dot Product Computation',
            metrics={
                'user_id': user_id,
                'num_items': num_items,
                'total_computation_time_sec': total_time,
                'average_computation_time_sec': avg_time,
                'throughput_items_per_sec': num_items / total_time,
                'min_computation_time_sec': float(np.min(computation_times)),
                'max_computation_time_sec': float(np.max(computation_times)),
                'encrypted_scores_size_kb': file_size / 1024
            },
            parameters={
                'encryption_scheme': 'CKKS',
                'operation': 'dot_product',
                'num_operations': num_items
            }
        )
        
        # 저장
        json_path = reporter.save_json()
        md_path = reporter.generate_markdown_report()
        
        logger.info(f"실험 결과 저장: {json_path}")
        logger.info(f"마크다운 리포트: {md_path}")
        
        logger.info("=" * 60)
        logger.info("서버 연산 완료!")
        logger.info("=" * 60)
        
    except Exception as e:
        log_exception(logger, e, "compute_encrypted_recommendations")
        raise

if __name__ == '__main__':
    import logging
    
    try:
        compute_encrypted_recommendations(user_id=0)
    except Exception as e:
        logger.critical("서버 연산 실패!")
        sys.exit(1)
