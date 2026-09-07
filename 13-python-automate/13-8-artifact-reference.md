# 13-8. 도구 검증과 아티팩트 해석 참고

이 절은 도구의 README와 공식 문서를 기준으로 실습의 의존성과 해석 범위를 정리합니다. 확인일은 **2026-09-07**입니다. 릴리스와 출력 형식은 바뀔 수 있으므로 실제 수업에는 사용한 버전·옵션·규칙 커밋을 별도로 기록합니다.

## 1. 제시된 통합 도구의 확인 결과

| 프로젝트 | 공식 자료에서 확인한 범위 | 교안에서의 사용 |
| --- | --- | --- |
| [cristianzsh/triager](https://github.com/cristianzsh/triager) | KAPE 등으로 수집한 아티팩트 처리, 여러 포렌식 도구 연계, CSV 정리, 다중 사건·호스트 작업 공간 | 오케스트레이션과 정규화 구조의 참고. 특정 ATT&CK 자동 매핑·스코어링은 별도 기능 검증 없이 보장하지 않음 |
| `mark-hallman/kape-report-generator` | 제시된 주소의 공개 README와 기능을 이번 확인에서 확보하지 못함 | 실행 의존성으로 채택하지 않음. 정확한 URL·소유자·문서 확인 필요 |
| `ANSSI-FR/UTMP` | 제시된 이름으로 공개 프로젝트와 설명을 이번 확인에서 검증하지 못함 | KAPE/UAC 통합 분석 도구로 확정해 소개하지 않음 |
| [ANSSI-FR/orc2timeline](https://github.com/ANSSI-FR/orc2timeline) | DFIR-ORC가 만든 아카이브의 아티팩트로 타임라인 생성 | 실제 확인된 별도 도구. UTMP와 같은 도구이거나 KAPE/UAC를 바로 지원한다고 간주하지 않음 |

triager의 현재 README는 KAPE·Velociraptor·Aralez 등의 수집 자료와 전용 유틸리티 연계를 설명합니다. 실제 수집 디렉터리의 레이아웃과 처리 프로필을 맞추어야 하며, “임의 KAPE 폴더를 넣으면 모두 처리된다”는 전제를 두지 않습니다. [Triager 공식 설명](https://github.com/cristianzsh/triager)

## 2. 아티팩트별 공식 엔진

| 목적 | 공식 프로젝트 | 구분할 점 |
| --- | --- | --- |
| KAPE 수집·처리 정의 | [KapeFiles](https://github.com/EricZimmerman/KapeFiles) | Targets·Modules 정의 저장소. KAPE 실행 파일과 라이선스를 동일시하지 않음 |
| EVTX 파싱 | [python-evtx](https://github.com/williballenthin/python-evtx) | EVTX 파서이며 Prefetch·Amcache용이 아님 |
| EVTX 변환 | [EvtxECmd](https://github.com/EricZimmerman/evtx) | 이벤트별 출력 필드·맵을 확인해 어댑터 작성 |
| 이벤트 탐지·타임라인 | [Hayabusa](https://github.com/Yamato-Security/hayabusa) | 엔진 버전·프로필·규칙에 따라 출력과 탐지 범위가 달라짐 |
| 포렌식 검색·Sigma 등 | [Chainsaw](https://github.com/WithSecureLabs/chainsaw) | 규칙·필드 매핑과 입력 범위를 확인 |
| Prefetch | [PECmd](https://github.com/EricZimmerman/PECmd) | 내보낸 실행 시각과 파일 참조 필드의 의미 확인 |
| Shimcache | [AppCompatCacheParser](https://github.com/EricZimmerman/AppCompatCacheParser) | Windows 버전별 구조와 시각 의미 확인 |
| Amcache | [AmcacheParser](https://github.com/EricZimmerman/AmcacheParser) | 인벤토리·파일 정보와 실행 확정 구분 |
| MFT·USN 등 | [MFTECmd](https://github.com/EricZimmerman/MFTECmd) | SI/FN 속성·엔트리·시퀀스·변경 사유 구분 |
| 레지스트리 | [RECmd](https://github.com/EricZimmerman/RECmd), [python-registry](https://github.com/williballenthin/python-registry) | 키 LastWrite와 개별 값의 변경·실행 시점을 동일시하지 않음 |
| 여러 데이터 소스 | [dissect.target](https://github.com/fox-it/dissect.target) | 디스크 이미지·파일 모음 접근과 플러그인별 기능을 확인 |

## 3. 이벤트 ID는 문맥과 함께 읽습니다

| 관찰 | 공식 설명 | 분석에 필요한 추가 문맥 |
| --- | --- | --- |
| 4624 | [로그온 성공](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4624) | 대상 호스트·대상 계정·LogonType·출발 주소 |
| 4625 | [로그온 실패](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4625) | 실패 사유·계정·주소·정상 반복 작업 |
| 4698 | [예약 작업 생성](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4698) | 작업 내용·실행 대상·트리거·승인 여부 |
| 4720 | [사용자 계정 생성](https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-10/security/threat-protection/auditing/event-4720) | Subject와 Target 계정·운영 승인 |
| Sysmon 1 | [Sysmon 문서](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon) | Provider·채널·프로세스·부모·설정에 따른 수집 여부 |

이벤트의 부재는 감사 정책, 보존 기간, 수집 누락, 로그 손실 때문일 수도 있습니다. 룰 일치가 없다는 이유로 행위가 없었다고 결론 내리지 않습니다.

## 4. 과잉 해석을 막는 질문

- Prefetch는 실행 흔적 해석에 활용되지만 모든 실행·사용자·정확한 행위 목적을 담는 것은 아닙니다.
- Shimcache·Amcache 항목만으로 실행을 단정하지 않고 OS 버전과 다른 근거를 대조합니다.
- MFT SI/FN 차이만으로 시간 조작을 확정하지 않습니다.
- 대량 USN 변경만으로 랜섬웨어라고 판정하지 않습니다.
- Run/RunOnce·작업·서비스 등록은 정상 기능에도 사용됩니다.
- ATT&CK는 분석 분류 체계입니다. [T1547.001 공식 설명](https://attack.mitre.org/techniques/T1547/001/)과 실제 관찰·규칙의 범위를 구분합니다.

## 5. 교사가 실제 자료를 연결할 때 확인할 항목

1. 파서·출력 프로필·헤더·시각 의미를 고정했는가?
2. 합성 테스트 외에 익명화된 실제 샘플로 열 매핑을 대조했는가?
3. 파싱 실패·시각 누락·미수집 상태가 보고서에서 사라지지 않는가?
4. 분석 결과의 근거를 원본 아티팩트까지 추적할 수 있는가?
5. 정상 관리 행위가 포함된 비교 자료로 과도한 검토 항목 발생을 평가했는가?

---

이전: [13-7. Windows 아티팩트 통합 분석](13-7-spreadsheet-report-project.md) · [13장 안내](../13-python-automate.md)
