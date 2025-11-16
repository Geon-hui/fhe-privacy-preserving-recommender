import sys
import time
import tenseal as ts
import yaml
from pathlib import Path

from logger import setup_logger, log_exception
from report_generator import ExperimentReporter

logger = setup_logger('keygen')

def load_config():
    try:
        logger.info("설정 파일 로드 중...")
        with open('config/params.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logger.debug(f"SEAL 파라미터: {config['seal']}")
        return config
    except Exception as e:
        log_exception(logger, e, "load_config")
        raise

def generate_keys():
    """CKKS 키 생성 with 결과 기록"""
    reporter = ExperimentReporter('key_generation')
    
    try:
        config = load_config()['seal']
        
        logger.info("=" * 60)
        logger.info("CKKS 컨텍스트 생성 시작")
        logger.info("=" * 60)
        
        logger.info(f"Poly modulus degree: {config['poly_modulus_degree']}")
        logger.info(f"Coeff modulus bit sizes: {config['coeff_mod_bit_sizes']}")
        logger.info(f"Scale: 2^{config['scale_bits']}")
        
        # 키 생성 시간 측정
        start_time = time.time()
        
        context = ts.context(
            ts.SCHEME_TYPE.CKKS,
            poly_modulus_degree=config['poly_modulus_degree'],
            coeff_mod_bit_sizes=config['coeff_mod_bit_sizes']
        )
        
        context_creation_time = time.time() - start_time
        logger.info(f"컨텍스트 생성 완료 ({context_creation_time:.3f}초)")
        
        context.global_scale = 2 ** config['scale_bits']
        logger.info(f"Global scale 설정: {context.global_scale}")
        
        # Galois keys
        galois_start = time.time()
        logger.info("Galois keys 생성 중...")
        context.generate_galois_keys()
        galois_time = time.time() - galois_start
        logger.info(f"Galois keys 생성 완료 ({galois_time:.3f}초)")
        
        # Relinearization keys
        relin_start = time.time()
        logger.info("Relinearization keys 생성 중...")
        context.generate_relin_keys()
        relin_time = time.time() - relin_start
        logger.info(f"Relinearization keys 생성 완료 ({relin_time:.3f}초)")
        
        # 키 디렉토리 생성
        key_dir = Path('keys')
        key_dir.mkdir(exist_ok=True)
        
        # 비밀키 저장
        secret_path = key_dir / 'secret_context.bin'
        logger.info(f"비밀키 저장 중: {secret_path}")
        with open(secret_path, 'wb') as f:
            f.write(context.serialize(save_secret_key=True))
        secret_size = secret_path.stat().st_size
        logger.info(f"비밀키 저장 완료 ({secret_size / 1024:.1f} KB)")
        
        # 공개키 저장
        context.make_context_public()
        public_path = key_dir / 'public_context.bin'
        logger.info(f"공개키 저장 중: {public_path}")
        with open(public_path, 'wb') as f:
            f.write(context.serialize())
        public_size = public_path.stat().st_size
        logger.info(f"공개키 저장 완료 ({public_size / 1024:.1f} KB)")
        
        total_time = time.time() - start_time
        
        # 결과 기록
        reporter.add_stage(
            'CKKS Key Generation',
            metrics={
                'context_creation_time_sec': context_creation_time,
                'galois_keys_generation_time_sec': galois_time,
                'relin_keys_generation_time_sec': relin_time,
                'total_time_sec': total_time,
                'secret_key_size_kb': secret_size / 1024,
                'public_key_size_kb': public_size / 1024,
                'total_key_size_kb': (secret_size + public_size) / 1024
            },
            parameters={
                'poly_modulus_degree': config['poly_modulus_degree'],
                'coeff_mod_bit_sizes': config['coeff_mod_bit_sizes'],
                'scale_bits': config['scale_bits'],
                'number_of_levels': len(config['coeff_mod_bit_sizes']) - 2,
                'max_slot_count': config['poly_modulus_degree'] // 2
            }
        )
        
        # JSON 저장
        json_path = reporter.save_json()
        logger.info(f"실험 결과 JSON 저장: {json_path}")
        
        # 마크다운 리포트 생성
        md_path = reporter.generate_markdown_report()
        logger.info(f"마크다운 리포트 생성: {md_path}")
        
        logger.info("=" * 60)
        logger.info("키 생성 완료!")
        logger.info("  - keys/secret_context.bin (클라이언트용)")
        logger.info("  - keys/public_context.bin (서버용)")
        logger.info(f"  - {json_path} (실험 결과)")
        logger.info(f"  - {md_path} (리포트)")
        logger.info("=" * 60)
        
        return context
        
    except Exception as e:
        log_exception(logger, e, "generate_keys")
        raise

if __name__ == '__main__':
    import logging
    
    try:
        generate_keys()
    except Exception as e:
        logger.critical("키 생성 실패!")
        sys.exit(1)
