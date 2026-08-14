![02 Python Setup](https://placehold.co/1500x400/c2410c/ffffff.png?text=02+Python+Setup&font=montserrat)
# 02. Python 설치 및 실습 환경 구성

## 개요
전 OS(Windows/macOS/Linux)에서 실습 환경을 구축한다. 두 가지 경로를 제시한다. 1안은 [python.org](http://python.org) 기본 설치 + venv 가상환경, 2안은 Anaconda/Miniconda 기반 환경이다.
{% hint style="info" %}
## 🧭 학습 목표
- 1안(기본 설치): [python.org](http://python.org) 설치 + venv로 격리된 실습 환경을 만든다
- 2안(아나콘다): conda 환경을 만들고 패키지를 관리한다
- requests/pwntools/pycryptodome 등 과정 필수 패키지를 설치한다
- 설치가 올바른지 검증 스크립트로 확인한다
{% endhint %}
---
# 2.1 기본 설치 ([python.org](http://python.org) + venv)

{% hint style="info" %}
시스템을 가볍게 유지하고 싶거나, 컴파일 의존성(pwntools 등)을 사용자 제어로 관리하고 싶을 때 선택한다. 보안 실무자에게는 가장 무난한 설치 경로다. 
**Windows**
1. [https://python.org/downloads](https://python.org/downloads) 접속 → 최신 3.x 설치 프로그램 다운로드
2. 설치 시작 화면에서 **반드시** 하단의 **이 박스를 체크**: `Add python.exe to PATH`
3. Install Now 클릭
```powershell
python --version
pip --version
winget install Python.Python.3.12   # winget 이용 대안 (Windows 10 1709+)
```
> 💡 `'python'은(는) 내부 또는 외부 명령...` 오류는 설치 시 PATH 추가 체크박스를 놓친 경우다. 설치 프로그램을 다시 실행해 `Modify` → PATH 옵션을 켜면 해결된다.
**macOS**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python3
python3 --version
pip3 --version
```
> 💡 macOS는 `python`/`python3`가 혼동되기 쉬우니 항상 `python3`/`pip3`로 명시한다.
**Linux**
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv   # Debian/Ubuntu/Kali
sudo dnf install -y python3 python3-pip                                    # RHEL/Fedora
sudo pacman -S python python-pip                                           # Arch
```
> 🎯 **Kali Linux / Parrot OS 사용자라면 **보안 실습용 배포판(Kali Linux, Parrot OS)은 Python 3와 pip이 이미 기본으로 설치되어 있어 위 설치 단계가 **별도로 필요 없다**. `python3 --version`으로 버전만 확인하고 바로 2.2절(venv 가상환경)로 넘어가면 된다. 본인 장비를 보안 실습용으로 따로 구성할 계획이라면, nmap·Burp Suite·pwntools 같은 도구가 미리 포함된 **Kali Linux 또는 Parrot OS 사용을 권장한다** — 이 커리큘럼 전체(pwntools CTF, 네트워크 진단, 포렌식 등)와 설치 부담 없이 바로 호환된다.
{% endhint %}

# 2.2 venv 가상환경 — 3개 OS 공통

{% hint style="success" %}
가상환경은 과정 전용 패키지를 시스템과 분리해 설치하는 상자다. 반드시 사용한다. **이 커리큘럼은 3장(기초교안)의 실습 폴더 구조와 동일하게 프로젝트 폴더명 ****`python-security-lab`****, 가상환경명 ****`.venv`****를 그대로 따른다.**
```bash
mkdir python-security-lab && cd python-security-lab
python3 -m venv .venv        # Windows: py -m venv .venv
source .venv/bin/activate          # macOS/Linux
.venv\Scripts\activate             # Windows (cmd)
.venv\Scripts\Activate.ps1         # Windows (PowerShell)
deactivate # 가상환경 비활성화 시
```
> ✅ **\[심화과정에서는\]** 이 venv 안에 이 과정 전체에 필요한 패키지가 다 들어간다. 랩을 새로 구성할 때마다 이 상자만 새로 만들면 시스템 Python은 항상 깨끗하게 유지된다.
{% endhint %}

# 2.3 아나콘다 (Anaconda/Miniconda)

{% hint style="info" %}
데이터 분석·과학 패키지가 미리 빌드된 배포본이다. 용량이 크므로(Anaconda 수 GB) 가벼운 **Miniconda**를 권장한다.
```bash
bash Miniconda3-latest-MacOSX-arm64.sh      # macOS Apple Silicon
bash Miniconda3-latest-Linux-x86_64.sh      # Linux
source ~/.bashrc
# Windows: Miniconda3-latest-Windows-x86_64.exe GUI 설치
```
```bash
conda create -n python-security-lab python=3.11 -y
conda activate python-security-lab
conda install requests beautifulsoup4 -y
pip install pwntools pycryptodome   # conda에 없는 패키지는 pip로
conda env list
conda env remove -n python-security-lab
```
| 항목 | 1안(venv) | 2안(conda) |
| --- | --- | --- |
| 용량 | 가벼움(수 MB) | 큼(수십 MB\~수 GB) |
| 패키지 관리 | pip만 | conda + pip 혼용 |
| 적합 대상 | pwntools/socket 중심(이 커리큘럼 기본) | numpy/pandas·ML 분석 병행 시 |

> 💡 이 커리큘럼은 의존 패키지가 가벼워 **1안(venv)을 기본**으로 사용한다. 대용량 데이터 분석처럼 numpy/pandas·로컬 LLM 의존성이 커지는 단계에서만 conda로 전환을 고려한다.
{% endhint %}

# 2.4 공통 패키지와 Jupyter

{% hint style="warning" %}
```bash
(venv) python -m pip install requests beautifulsoup4 lxml pwntools pycryptodome scapy jupyter ipykernel
```
> 💡 **pwntools와 Windows**: Linux/macOS 공식 지원. Windows는 WSL2(`wsl --install -d Ubuntu`) 안에서 위 Linux 항목을 그대로 따르는 것을 권장한다.
> 📦 **더 읽어보기**: [Python 패키징 도구 비교 — pip vs uv vs Poetry](https://app.notion.com/p/3b3436c34cbd8199a9a4f46946dc6ef8) — 잠금 파일이 왜 필요한지, 새 프로젝xd8b8에서 uv를 쓸지 여부를 실측 및 실제 명령어로 다루는 보충 아티클.
```bash
(venv) python -m ipykernel install --user --name python-security-lab --display-name "Python (python-security-lab)"
(venv) jupyter notebook   # 또는 jupyter lab
```
기초부터 캡스톤까지 실행 가능한 MyST Markdown 노트북으로 구성한 Jupyter Book을 프로젝트 폴더에 제공한다. Notion 각 과정 페이지 하단에도 핵심 실습 셀을 직접 수록해 별도 파일 없이 내용을 확인할 수 있다.
{% hint style="success" %}
# 🧪 직접 해보기
> 📝 **연습**: 아래 검증 스크립트를 본인 환경에 저장해 실행하고, 누락된 패키지가 있다면 `pip install`로 설치해 전부 `[OK]`가 뜨게 만들어라.
```python
import sys
assert sys.version_info >= (3, 9), "Python 3.9 이상 필요"
for mod in ["requests", "bs4", "Crypto", "pwn"]:
    try:
        __import__(mod); print(f"[OK] {mod}")
    except ImportError:
        print(f"[없음] {mod}")
```

**풀이 보기**

*[풀이 이미지 생략]*
	`[없음]`으로 뜨는 모듈은 다음 매핑으로 설치한다.
	```bash
pip install requests beautifulsoup4 pycryptodome pwntools
	```
	모듈명과 패키지명이 다른 경우에 주의한다: `bs4` 모듈은 `beautifulsoup4` 패키지, `Crypto` 모듈은 `pycryptodome` 패키지, `pwn` 모듈은 `pwntools` 패키지다. 이 이름 불일치는 파이썬 생태계에서 자주 겪는 함정이다.
	핵심: 설치 검증은 "import가 되는지"로 확인하는 것이 가장 확실하다. `pip list`만으로는 실제 코드에서 import가 되는지 보장하지 못한다(예: 대소문자, 버전 충돌).

{% endhint %}

---
{% hint style="info" %}
# 🧰 Jupyter Book 빌드 실습
```bash
cd whitehat-jupyter-book
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python .venv/bin/jupyter-book build book
```
```python
import platform
import sys
print(sys.executable)
print(sys.version)
print(platform.platform())
assert sys.version_info >= (3, 11)
```
**문제 해결 순서**
1. `sys.executable`이 가상환경 아래인지 확인한다.
2. `python -m pip --version`이 같은 Python을 가리키는지 확인한다.
3. 노트북 커널과 패키지 설치 환경이 같은지 확인한다.
{% endhint %}
---
[3. Python 문법 기초교안](https://zxz3650.gitbook.io/python-basic/03-python-basics)으로 이동한다