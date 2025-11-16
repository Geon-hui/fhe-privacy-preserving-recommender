#!/bin/bash

echo "======================================"
echo "FHE 프로젝트 로그 확인"
echo "======================================"

LOG_DIR="logs"

if [ ! -d "$LOG_DIR" ]; then
    echo "로그 디렉토리가 없습니다: $LOG_DIR"
    exit 1
fi

echo ""
echo "[전체 로그 파일 목록]"
ls -lh $LOG_DIR/

echo ""
echo "[최신 에러 로그 (최근 20줄)]"
for error_log in $LOG_DIR/*_errors.log; do
    if [ -f "$error_log" ]; then
        echo "--- $error_log ---"
        tail -20 "$error_log"
        echo ""
    fi
done

echo ""
echo "[전체 로그 파일 크기]"
du -sh $LOG_DIR/

echo "======================================"
echo "로그 파일 위치: $LOG_DIR"
echo "======================================"
