import numpy as np
import tenseal as ts
import pickle
import yaml

def load_secret_context():
    with open('keys/secret_context.bin', 'rb') as f:
        return ts.context_from(f.read())

def load_config():
    with open('config/params.yaml', 'r') as f:
        return yaml.safe_load(f)

def decrypt_and_recommend(user_id=0):
    """복호화 및 Top-K 추천"""
    context = load_secret_context()
    config = load_config()['recommendation']
    
    # 암호화된 점수 로드
    with open(f'data/encrypted/scores_user_{user_id}.npy', 'rb') as f:
        encrypted_scores_ser = pickle.load(f)
    
    # 복호화
    print("점수 복호화 중...")
    scores = []
    for enc_ser in encrypted_scores_ser:
        enc = ts.ckks_vector_from(context, enc_ser)
        scores.append(enc.decrypt()[0])
    
    scores = np.array(scores)
    
    # 임계값 필터링
    threshold = config['threshold']
    filtered_indices = np.where(scores >= threshold)[0]
    print(f"임계값 {threshold} 이상인 아이템: {len(filtered_indices)}개")
    
    # Top-K 선택
    top_k = config['top_k']
    if len(filtered_indices) > 0:
        filtered_scores = scores[filtered_indices]
        top_k_in_filtered = np.argsort(filtered_scores)[-top_k:][::-1]
        top_k_indices = filtered_indices[top_k_in_filtered]
    else:
        top_k_indices = np.argsort(scores)[-top_k:][::-1]
    
    # 결과 출력
    item_ids = np.load('data/processed/item_ids.npy')
    print(f"\n사용자 {user_id}에 대한 Top-{top_k} 추천:")
    for rank, idx in enumerate(top_k_indices, 1):
        print(f"  {rank}. 영화 ID {item_ids[idx]} (점수: {scores[idx]:.4f})")
    
    return top_k_indices, scores[top_k_indices]

if __name__ == '__main__':
    decrypt_and_recommend(user_id=0)
