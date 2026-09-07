# 13-2. KAPE 결과 구조와 증거 목록

> **핵심 질문** · CSV가 여러 개 있을 때, 어느 호스트의 어떤 원본에서 나온 결과인지 어떻게 알 수 있을까요?

KAPE의 Target(`.tkape`)은 수집할 아티팩트를 정의하고 Module(`.mkape`)은 도구를 실행해 수집 자료를 처리하는 작업을 정의합니다. `kape.exe`는 명령줄 실행에, `gkape.exe`는 GUI 구성에 사용됩니다. 수집 결과가 항상 CSV인 것은 아닙니다. EVTX·레지스트리 하이브 등은 전용 파서를 거쳐야 합니다. [KapeFiles 공식 저장소](https://github.com/EricZimmerman/KapeFiles)

## 1. 입력·중간 결과·출력 폴더를 분리합니다

```text
case-001/
├── evidence/             수집 원본: EVTX, Prefetch, 하이브, MFT 등
├── parsed/               파서가 만든 CSV·JSON과 파서 실행 로그
├── intake/
│   ├── manifest.json     어떤 파일을 어떤 의미로 읽을지 선언
│   └── exports/          승인된 CSV 작업 사본
└── analysis-run-001/     Python 분석 결과; 기존 결과와 별도
```

이는 교안의 권장 작업 구조이며 KAPE의 고정 출력 디렉터리 규격이 아닙니다. Target·Module·실행 옵션에 따라 실제 구조가 달라질 수 있습니다.

## 2. manifest는 파일 이름 추측을 없앱니다

```json
{
  "schema_version": 1,
  "case_id": "CASE-001",
  "sources": [
    {
      "id": "host-a-security",
      "host": "HOST-A",
      "artifact": "evtx",
      "path": "exports/security.csv",
      "parser": "사용한 파서 이름",
      "parser_version": "실제 버전",
      "timestamp_kind": "event_created",
      "columns": {
        "timestamp": "TimeCreated",
        "event_id": "EventId",
        "channel": "Channel",
        "provider": "Provider",
        "record_id": "EventRecordId",
        "user": "TargetUser",
        "src_ip": "SourceAddress",
        "logon_type": "LogonType"
      }
    }
  ]
}
```

오른쪽 열 이름은 **매핑 방법을 설명하기 위한 예**입니다. 특정 EvtxECmd 버전의 실제 헤더라고 가정하지 않습니다. 실제 CSV 헤더를 확인해 바꾸어야 하며, 이벤트별 값이 복합 필드에 들어 있다면 별도 어댑터가 먼저 필요합니다.

`host`는 수집 자료의 원래 호스트입니다. 분석을 수행하는 PC 이름으로 채우지 않습니다. 도메인 계정·SID와 호스트별 로컬 계정은 구분하고, 별칭을 자동으로 같은 사용자로 합치지 않습니다.

## 3. 원본으로 되돌아갈 수 있어야 합니다

예제는 CSV 바이트의 SHA-256, 파일 상대 경로, 헤더를 1로 센 레코드 번호를 정규화 행마다 저장합니다. 줄바꿈이 포함된 CSV 셀은 여러 줄을 차지할 수 있으므로 레코드 번호는 물리적 줄 번호와 다릅니다.

CSV 해시는 **분석에 입력된 CSV의 동일성**을 확인합니다. 수집 원본 EVTX의 해시나 적법한 증거 인계 기록을 대신하지 않습니다. 실제 사건에는 원본 아티팩트 경로·해시·수집 시각·수집 도구 버전·인계 기록을 별도로 연결합니다.

## 4. 누락과 0건의 차이

| 상태 | 의미 |
| --- | --- |
| `processed` | 헤더와 모든 행을 처리함 |
| `empty` | 유효한 헤더가 있으나 데이터 행이 없음 |
| `partial` | 유효한 행과 격리한 오류 행이 함께 있음 |
| `parse_failed` | 인코딩·CSV 형식·헤더 계약 오류 |
| `missing` | manifest에 선언한 파일을 받지 못함 |

manifest에 선언하지 않은 자료의 수집 여부는 알 수 없습니다. 기본 프로그램이 디스크 전체를 검색하거나 필요한 자료를 자동으로 찾아내는 것은 아닙니다.

## 실습

1. 합성 자료를 생성하고 manifest와 실제 CSV 헤더를 나란히 읽습니다.
2. 존재하지 않는 `amcache.csv`가 왜 `missing`인지 설명합니다.
3. 헤더만 있는 파일과 헤더가 틀린 파일을 만들어 각각의 상태를 비교합니다.

- [ ] 수집 원본·파서 결과·분석 결과를 구분합니다.
- [ ] 자료별 호스트·파서·열 매핑이 선언되어 있습니다.
- [ ] 해시만으로 증거의 모든 신뢰성을 보장한다고 설명하지 않습니다.

---

다음: [13-3. 아티팩트 파서와 분석 엔진 연계](13-3-web-collection.md)
