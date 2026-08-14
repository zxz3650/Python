# 05-9. 웹 로그 분석

04장의 대용량 파일 처리와 05장의 문자열·정규표현식·날짜 처리를 연결해 Apache/Nginx Combined Log 형식의 웹 접근 로그를 분석합니다. 전체 파일을 하나의 DataFrame으로 읽지 않고 한 줄씩 파싱한 뒤 일정한 배치 단위로 집계합니다.

{% hint style="info" %}
## 🧭 학습 목표

- 약 3GB 로그를 전체 메모리에 적재하지 않고 처리합니다.
- Combined Log 형식을 정규표현식으로 구조화합니다.
- 파싱 성공·실패 건수와 데이터 품질을 검증합니다.
- 상태 코드·메서드·IP·경로·시간대별 요청량을 집계합니다.
- 반복 404와 민감 경로 요청을 후속 조사 후보로 선별합니다.
- 분석 결과를 CSV와 JSON으로 재현 가능하게 저장합니다.
{% endhint %}

## 선행 지식

- 04-6의 스트리밍 처리와 오류 보존
- 05-8의 DataFrame과 청크 처리
- 05-3부터 05-6까지의 정규표현식·검증·날짜 처리

## 실습 파일

- [Jupyter Notebook 내려받기](https://github.com/zxz3650/Python/blob/master/notebooks/05-9-web-log-analysis.ipynb)
- [Google Colab에서 열기](https://colab.research.google.com/github/zxz3650/Python/blob/master/notebooks/05-9-web-log-analysis.ipynb)

{% hint style="warning" %}
실제 로그에는 IP 주소, 요청 경로, 식별자 등 민감 정보가 포함될 수 있습니다. 조직의 승인·보존·반출 정책을 확인하고 원본 로그는 읽기 전용으로 다룹니다.
{% endhint %}

## 분석 관점과 코드 연결

웹 로그에는 하나의 정답이 들어 있지 않습니다. 먼저 어떤 질문에 답할 것인지 정한 뒤 그 질문에 필요한 필드와 지표를 선택해야 합니다. 이 실습은 다음 다섯 관점으로 로그를 분석합니다.

| 분석 관점 | 답하려는 질문 | 핵심 지표 | 주요 코드 |
| --- | --- | --- | --- |
| 데이터 신뢰성 | 분석에 사용할 수 있는 로그인가? | 전체·정상·오류 행, 오류율 | `parse_combined_log()`, `assert` |
| 서비스 상태 | 서버가 정상적으로 응답했는가? | 상태 코드, 응답 바이트 | `value_counts()`, `Counter.update()` |
| 이용 패턴 | 누가 언제 무엇을 요청했는가? | 메서드·IP·경로·시간대 | `urlsplit()`, UTC 변환, `Counter` |
| 보안 조사 | 추가 확인이 필요한 요청은 무엇인가? | IP별 404, 민감 경로 요청 | 정규표현식 마스크, 임계값 필터 |
| 처리 성능 | 3GB급 파일을 안정적으로 반복 분석할 수 있는가? | 처리 시간, 처리량, 배치 크기 | 스트리밍 반복문, `BATCH_SIZE` |

{% hint style="info" %}
분석 순서는 **데이터 신뢰성 → 서비스 상태·이용 패턴 → 보안 조사**입니다. 파싱 오류가 많은 데이터를 먼저 보안 관점으로 해석하면 잘못된 결론을 만들 수 있습니다.
{% endhint %}

### 관점 A. 데이터 신뢰성

가장 먼저 “몇 행을 읽었고 몇 행을 해석하지 못했는가?”를 확인합니다.

```python
summary["total_lines"] += 1

try:
    batch.append(parse_combined_log(line))
except ValueError:
    summary["malformed_lines"] += 1
```

분석이 끝난 뒤 다음 검증으로 누락 여부를 확인합니다.

```python
assert summary["total_lines"] == (
    summary["parsed_lines"] + summary["malformed_lines"]
)
```

이 검증이 실패하면 상태 코드나 IP 순위를 해석하기 전에 처리 로직부터 수정해야 합니다.

### 관점 B. 서비스 상태

상태 코드는 웹 서비스가 요청을 어떻게 처리했는지 보여 줍니다.

```python
summary["status"].update(
    frame["status"].value_counts().to_dict()
)
summary["total_bytes"] += int(frame["bytes"].sum())
```

- `2xx`: 정상 처리 여부
- `3xx`: 리다이렉션 동작
- `4xx`: 잘못된 요청, 없는 경로, 인증 문제
- `5xx`: 서버 내부 오류 가능성

단, `404`가 많다는 사실만으로 공격이라고 판단하지 않습니다. 잘못된 링크나 배포 직후 정적 파일 누락도 원인이 될 수 있습니다.

### 관점 C. 이용 패턴

“어떤 IP가 언제 어떤 경로를 요청했는가?”를 집계해 평상시 트래픽의 형태를 파악합니다.

```python
request_path = urlsplit(fields["target"]).path or "/"
timestamp = datetime.strptime(
    fields["timestamp"],
    "%d/%b/%Y:%H:%M:%S %z",
).astimezone(timezone.utc)
```

`urlsplit()`은 `/login?next=/admin`에서 경로 `/login`을 분리해 같은 기능의 요청을 묶습니다. 시간은 UTC로 통일해야 서로 다른 시간대의 로그를 같은 기준으로 비교할 수 있습니다.

```python
summary["method"].update(frame["method"].value_counts())
summary["ip"].update(frame["ip"].value_counts())
summary["path"].update(frame["path"].value_counts())
summary["hour"].update(frame["hour"].value_counts())
```

상위값은 이상 행위를 확정하는 결과가 아니라 평상시 패턴과 비교할 기준입니다.

### 관점 D. 보안 조사 우선순위

이 실습에서는 두 가지 신호를 조합합니다.

1. 한 IP에서 반복적으로 발생한 `404`
2. `.env`, `.git`, `wp-admin`, `phpmyadmin` 같은 민감 경로 요청

```python
not_found = frame.loc[frame["status"] == 404, "ip"]
summary["not_found_by_ip"].update(
    not_found.value_counts().to_dict()
)

sensitive_mask = frame["path"].str.contains(
    SENSITIVE_PATH_PATTERN,
    regex=True,
    na=False,
)
```

이후 두 신호 중 하나라도 임계값을 넘은 IP를 후보로 만듭니다.

```python
if (
    not_found_count >= not_found_threshold
    or sensitive_count >= sensitive_path_threshold
):
    triage_rows.append(candidate)
```

여기서 `or`를 사용한 이유는 두 신호를 모두 만족하지 않더라도 반복 404 또는 민감 경로 집중 중 하나가 뚜렷하면 후속 확인 가치가 있기 때문입니다. 후보는 침해 확정이 아니며 원본 요청, 프록시 구조, 승인된 스캐너 정보를 함께 확인해야 합니다.

### 관점 E. 대용량 처리 성능

파일 전체 대신 일정한 수의 행만 DataFrame으로 만듭니다.

```python
for line in file:
    batch.append(parse_combined_log(line))

    if len(batch) >= BATCH_SIZE:
        merge_batch(summary, batch)
        batch.clear()
```

- `batch`: 현재 처리 중인 일부 행
- `merge_batch()`: 배치 통계를 전체 집계에 누적
- `batch.clear()`: 처리한 상세 행을 메모리에서 제거
- `Counter`: 전체 상세 로그 대신 항목별 개수만 유지

처리 속도는 다음처럼 계산합니다.

```python
throughput_mb_s = (
    LOG_PATH.stat().st_size / (1024 ** 2) / elapsed_seconds
)
```

이 값은 저장장치, CPU, 로그 형식에 따라 달라지므로 다른 환경의 절대값보다 같은 환경에서 배치 크기를 바꿨을 때의 차이를 비교합니다.


## 1. 왜 전체 파일을 DataFrame으로 읽지 않는가

약 3GB 텍스트 파일은 DataFrame으로 변환될 때 문자열 객체, 인덱스, 열별 자료구조가 추가되어 파일 크기보다 훨씬 많은 메모리를 사용할 수 있습니다.

이 실습에서는 다음 구조를 사용합니다.

```text
로그 파일
→ 한 줄 읽기
→ 정규표현식 파싱·자료형 변환
→ 최대 100,000행 배치
→ DataFrame 배치 집계
→ Counter에 누적
→ 배치 메모리 해제
→ CSV·JSON 결과 저장
```

메모리 사용량은 전체 파일 크기보다 배치 크기와 고유 IP·경로의 개수에 주로 영향을 받습니다.

## 2. 입력 로그 형식

기본 입력은 Apache/Nginx Combined Log 형식입니다.

```text
203.0.113.10 - - [14/Aug/2026:10:30:00 +0900] "GET /login HTTP/1.1" 200 443 "-" "Mozilla/5.0"
```

추출하는 필드는 다음과 같습니다.

| 필드 | 의미 | 변환 |
| --- | --- | --- |
| IP | 요청 출발지 주소 | 문자열 |
| timestamp | 요청 발생 시각 | UTC datetime |
| method | HTTP 요청 메서드 | 문자열 |
| target | 쿼리 문자열을 포함한 요청 대상 | 문자열 |
| path | 쿼리 문자열을 제외한 경로 | 문자열 |
| status | HTTP 응답 상태 코드 | 정수 |
| bytes | 응답 크기 | 정수 |
| user agent | 클라이언트 식별 문자열 | 문자열 |

실제 로그 형식이 다르면 파서를 억지로 완화하기 전에 웹 서버의 `log_format` 설정을 먼저 확인합니다.

## 3. 실행 모드

노트북은 두 가지 모드를 제공합니다.

### 기본 학습 모드

```python
RUN_FULL_DATASET = False
```

- 합성 로그 20,001행을 자동 생성합니다.
- 민감 경로 탐색 형태의 교육용 이벤트와 오류 행 1개가 포함됩니다.
- 전체 분석·품질 검증·결과 저장을 빠르게 실행할 수 있습니다.

### 약 3GB 실제 로그 모드

```python
RUN_FULL_DATASET = True
FULL_LOG_PATH = Path("data/access-3gb.log")
BATCH_SIZE = 100_000
```

처음에는 `BATCH_SIZE = 50_000`으로 실행한 뒤 메모리 사용량을 확인하며 조정합니다. 배치가 크다고 항상 전체 처리 속도가 비례해 증가하지는 않습니다.

## 4. 분석 항목

노트북은 다음 결과를 생성합니다.

- 상태 코드별 요청 수
- HTTP 메서드별 요청 수
- 요청량 상위 IP
- 요청량 상위 경로
- UTC 시간대별 요청 수
- User-Agent별 요청 수
- IP별 404 발생 수
- 민감 경로 요청 후보
- 파싱 실패 행과 제한된 원문 예시
- 처리 시간과 초당 처리량

## 5. 데이터 품질 검증

다음 관계가 항상 성립해야 합니다.

```python
전체 행 수 == 정상 파싱 행 수 + 파싱 실패 행 수
정상 파싱 행 수 == 상태 코드 집계 합계
정상 파싱 행 수 == 메서드 집계 합계
```

오류율이 높을 때 확인할 순서:

1. Apache/Nginx 로그 형식
2. 텍스트 인코딩
3. 여러 줄로 기록된 예외 데이터
4. 로테이션 중 잘린 행
5. 프록시나 애플리케이션이 추가한 필드
6. 정규표현식과 자료형 변환 규칙

## 6. 보안 관점의 해석

반복 404, 높은 요청량, 민감 경로 접근은 조사 신호이지 침해의 증거가 아닙니다.

함께 확인할 정보:

- NAT·프록시·로드밸런서 구조
- 승인된 취약점 스캐너와 모니터링 도구
- 요청이 발생한 정확한 시간 범위
- 응답 상태와 응답 크기
- 동일 IP의 정상 요청 비율
- User-Agent와 세션·인증 이벤트
- 대상 서버와 애플리케이션의 역할

{% hint style="danger" %}
IP 주소 하나를 사용자 한 명으로 단정하거나, 임계값을 넘었다는 이유만으로 악성으로 확정하지 않습니다. 이 실습의 후보 목록은 원본 이벤트를 다시 확인하기 위한 우선순위입니다.
{% endhint %}

## 7. 산출물

실행 후 `outputs/web-log-analysis`에 다음 파일이 생성됩니다.

| 파일 | 내용 |
| --- | --- |
| `quality_report.csv` | 처리 건수·오류율·처리 시간 |
| `status_counts.csv` | 상태 코드별 요청 수 |
| `method_counts.csv` | 메서드별 요청 수 |
| `top_ips.csv` | 요청량 상위 IP |
| `top_paths.csv` | 요청량 상위 경로 |
| `hourly_requests.csv` | 시간대별 요청 수 |
| `triage_candidates.csv` | 후속 조사 후보 |
| `summary.json` | 자동화에 사용할 핵심 요약 |

## 8. 확장 과제

1. 특정 시간 범위만 분석하는 시작·종료 시각 필터를 추가합니다.
2. IPv4와 IPv6 주소 형식을 검증합니다.
3. 상태 코드 그룹을 `2xx`, `3xx`, `4xx`, `5xx`로 집계합니다.
4. 단위 시간별 404 비율이 급증한 구간을 찾습니다.
5. `.gz` 로테이션 로그를 스트리밍으로 읽습니다.
6. 여러 로그 파일의 집계를 하나의 결과로 병합합니다.
7. 08장의 명령줄 인자와 연결해 재사용 가능한 분석 프로그램으로 변환합니다.

## 완료 기준

- [ ] 전체 파일을 메모리에 올리지 않고 분석할 수 있습니다.
- [ ] 파서의 정상·오류 입력을 먼저 검증할 수 있습니다.
- [ ] 전체·정상·오류 행 수를 대조할 수 있습니다.
- [ ] IP·경로·상태 코드·시간대 집계를 생성할 수 있습니다.
- [ ] 조사 후보와 침해 확정을 구분해 설명할 수 있습니다.
- [ ] 다른 환경에서 재실행 가능한 Notebook과 결과 파일을 남길 수 있습니다.

---

다음 장: [06. 네트워크 프로그래밍](../06-network-programming.md)
