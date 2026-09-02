# 05장 실습 fixture

모든 파일은 교육용 합성 데이터이며 실제 계정·IP·토큰을 포함하지 않는다.

| 파일 | 연결 절 | 경계 사례 |
| --- | --- | --- |
| `normalization-cases.txt` | 05-1 | 양끝 공백, 분해된 유니코드, 대소문자 민감 경로 |
| `delimited-events.txt` | 05-2 | 메시지 내 구분자, 필드 수 오류 |
| `regex-cases.txt` | 05-3 | 전체 일치와 부분 검색 |
| `event-lines.txt` | 05-4 | 이름 있는 그룹, 형식 오류 |
| `validation-records.jsonl` | 05-5 | 계정·IP·허용값·점수·경로·JSON 문법 오류 |
| `timestamp-events.jsonl` | 05-6 | 시간대, `Z`, naive, 존재하지 않는 날짜 |
| `measurements.csv` | 05-7 | NaN, 숫자 변환 실패, 임계값 |
| `items.csv`, `large_items.csv` | 05-8 | 자료형 오류, 결측치, 청크 집계 |
| `web-access.log` | 05-9 | 정상·오탐·IPv6·CRLF·형식·의미 오류 |
| `web-access-invalid-utf8.log` | 05-9 | UTF-8 strict 디코딩 오류 |

`web-access-invalid-utf8.log`는 의도적으로 잘못된 바이트를 포함하므로 텍스트 편집기에서 재저장하지 않는다.
