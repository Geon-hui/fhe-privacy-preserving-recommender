import sys
import time
import numpy as np
import tenseal as ts
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / 'utils'))
from logger import setup_logger, log_exception
from report_generator import ExperimentReporter

logger = setup_logger('encrypt')

def load_secret_context():
    """비밀키 컨텍스트 로드"""
    try:
        context_path = Path('keys/secret_context.bin')
        logger.info(f"비밀키 컨텍스트 로드: {context_path}")
        
        if not context_path.exists():
            raise FileNotFoundError(f"비밀키 파일이 없습니다: {context_path}")
        
        with open(context_path, 'rb') as f:
            context = ts.context_from(f.read())
        
        logger.info("비밀키 컨텍스트 로드 완료")
        return context
        
    except Exception as e:
        log_exception(logger, e, "load_secret_context")
        raise

def encrypt_user_vector(user_id=0):
    """사용자 벡터 암호화 with 결과 기록"""
    reporter = ExperimentReporter('encryption')
    
    try:
        logger.info("=" * 60)
        logger.info(f"사용자 {user_id} 벡터 암호화 시작")
        logger.info("=" * 60)
        
        context = load_secret_context()
        
        user_vectors_path = Path('data/processed/user_vectors.npy')
        logger.info(f"사용자 벡터 로드: {user_vectors_path}")
        user_vectors = np.load(user_vectors_path)
        
        logger.info(f"전체 사용자 수: {len(user_vectors)}")
        
        if user_id >= len(user_vectors):
            raise ValueError(f"유효하지 않은 사용자 ID: {user_id} (최대: {len(user_vectors)-1})")
        
        user_vector = user_vectors[user_id]
        vector_dim = len(user_vector)
        vector_stats = {
            'min': float(user_vector.min()),
            'max': float(user_vector.max()),
            'mean': float(user_vector.mean()),
            'std': float(user_vector.std())
        }
        
        logger.info(f"사용자 {user_id} 벡터 차원: {vector_dim}")
        logger.info(f"벡터 통계: min={vector_stats['min']:.4f}, max={vector_stats['max']:.4f}, mean={vector_stats['mean']:.4f}")
        
        # 암호화 시간 측정
        logger.info("CKKS 암호화 수행 중...")
        start_time = time.time()
        
        encrypted_user = ts.ckks_vector(context, user_vector.tolist())
        
        encrypt_time = time.time() - start_time
        logger.info(f"암호화 소요 시간: {encrypt_time:.3f}초")
        
        # 저장
        output_dir = Path('data/encrypted')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f'user_{user_id}.bin'
        with open(output_path, 'wb') as f:
            f.write(encrypted_user.serialize())
        
        file_size = output_path.stat().st_size
        plaintext_size = user_vector.nbytes
        compression_ratio = file_size / plaintext_size
        
        logger.info(f"암호문 저장: {output_path} ({file_size / 1024:.1f} KB)")
        logger.info(f"압축률: {compression_ratio:.2f}x")
        
        # 결과 기록
        reporter.add_stage(
            'Vector Encryption',
            metrics={
                'user_id': user_id,
                'vector_dimension': vector_dim,
                'encryption_time_sec': encrypt_time,
                'plaintext_size_bytes': plaintext_size,
                'ciphertext_size_bytes': file_size,
                'ciphertext_size_kb': file_size / 1024,
                'size_expansion_ratio': compression_ratio,
                'vector_min': vector_stats['min'],
                'vector_max': vector_stats['max'],
                'vector_mean': vector_stats['mean'],
                'vector_std': vector_stats['std']
            },
            parameters={
                'encryption_scheme': 'CKKS',
                'output_path': str(output_path)
            }
        )
        
        # 저장
        json_path = reporter.save_json()
        md_path = reporter.generate_markdown_report()
        
        logger.info(f"실험 결과 저장: {json_path}")
        logger.info(f"마크다운 리포트: {md_path}")
        
        logger.info("=" * 60)
        logger.info("암호화 완료!")
        logger.info("=" * 60)
        
        return encrypted_user
        
    except Exception as e:
        log_exception(logger, e, "encrypt_user_vector")
        raise

if __name__ == '__main__':
    import logging
    
    try:
        encrypt_user_vector(user_id=0)
    except Exception as e:
        logger.critical("암호화 실패!")
        sys.exit(1)
