import json
import yaml
import time
from datetime import datetime
from pathlib import Path
import numpy as np

class ExperimentReporter:
    """실험 결과를 JSON과 마크다운으로 자동 기록"""
    
    def __init__(self, experiment_name):
        self.experiment_name = experiment_name
        self.start_time = time.time()
        self.results_dir = Path('results')
        self.results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.experiment_id = f"{experiment_name}_{timestamp}"
        
        self.data = {
            'experiment_id': self.experiment_id,
            'experiment_name': experiment_name,
            'timestamp': datetime.now().isoformat(),
            'stages': []
        }
    
    def add_stage(self, stage_name, metrics, parameters=None):
        """스테이지별 결과 추가"""
        stage_data = {
            'stage': stage_name,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'parameters': parameters or {}
        }
        self.data['stages'].append(stage_data)
    
    def save_json(self):
        """JSON 형식으로 저장"""
        json_path = self.results_dir / f'{self.experiment_id}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        return json_path
    
    def generate_markdown_report(self):
        """마크다운 리포트 생성"""
        md_path = self.results_dir / f'{self.experiment_id}_report.md'
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# 동형암호 기반 추천 시스템 실험 리포트\n\n")
            f.write(f"**실험 ID**: {self.experiment_id}\n\n")
            f.write(f"**실험 날짜**: {self.data['timestamp']}\n\n")
            f.write(f"**실험 시간**: {time.time() - self.start_time:.2f}초\n\n")
            f.write("---\n\n")
            
            # 각 스테이지 결과
            for idx, stage in enumerate(self.data['stages'], 1):
                f.write(f"## {idx}. {stage['stage']}\n\n")
                
                if stage['parameters']:
                    f.write("### 파라미터\n\n")
                    for key, value in stage['parameters'].items():
                        f.write(f"- **{key}**: {value}\n")
                    f.write("\n")
                
                f.write("### 결과\n\n")
                for key, value in stage['metrics'].items():
                    if isinstance(value, float):
                        f.write(f"- **{key}**: {value:.4f}\n")
                    else:
                        f.write(f"- **{key}**: {value}\n")
                f.write("\n---\n\n")
            
            # 요약
            f.write("## 실험 요약\n\n")
            f.write(f"- 총 {len(self.data['stages'])}개 스테이지 완료\n")
            f.write(f"- 전체 실행 시간: {time.time() - self.start_time:.2f}초\n")
            f.write(f"- 실험 날짜: {self.data['timestamp']}\n")
        
        return md_path

def load_experiment_config():
    """실험 설정 로드"""
    with open('config/params.yaml', 'r') as f:
        return yaml.safe_load(f)
