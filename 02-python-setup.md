![02 Python Setup](https://placehold.co/1500x400/c2410c/ffffff.png?text=02+Python+Setup&font=montserrat)

# 02. 개발 및 실습 환경

Python 코드를 같은 조건에서 반복 실행할 수 있도록 실습 환경을 구성한다. 이 과정은 Python 3.10 이상을 지원하며, 교안과 실습 예제는 Python 3.12 사용을 권장한다. 기본 경로는 Python 표준 가상환경인 `venv`이며, 기존에 conda를 사용하는 학습자를 위한 선택 경로도 함께 제시한다.

{% hint style="info" %}
### 🧭 학습 목표

- 운영체제에서 사용할 Python 버전을 확인한다.
- 과정 전용 `.venv` 가상환경을 만들고 활성화한다.
- `python -m pip`로 현재 가상환경에 패키지를 설치한다.
- `requirements.txt`로 공통 실습 패키지를 한 번에 설치한다.
- JupyterLab에서 올바른 Python 커널을 선택한다.
- Python 실행 파일과 패키지 설치 위치가 일치하는지 검증한다.
{% endhint %}

## 2.1 먼저 설치 경로 선택하기

처음 학습한다면 `venv` 경로를 사용한다. 이미 Anaconda나 Miniconda로 환경을 관리하고 있다면 conda 경로를 선택할 수 있다. 두 환경을 한 프로젝트에서 겹쳐 사용하지 않는다.

| 경로 | 권장 대상 | 진행 순서 |
| --- | --- | --- |
| Python + `venv` | 처음 시작하는 학습자, 이 과정의 기본 실습 | 2.2 → 2.3 → 2.4 → 2.6 → 2.7 → 2.8 |
| Miniconda + conda 환경 | 기존 conda 사용자, 별도의 conda 환경이 필요한 학습자 | 2.2 → 2.5 → 2.6 → 2.7 → 2.8 |

이 장을 마치면 교안 저장소의 프로젝트 루트에 다음과 같은 실습 자료가 준비된다. `.venv`는 기본 `venv` 경로를 선택했을 때만 생성되며, conda 환경은 저장소 밖의 conda 환경 디렉터리에서 관리된다.

```text
Python/
├── .venv/              # venv 경로에서만 생성, Git에 저장하지 않음
├── requirements.txt    # 핵심 과정 의존성
├── notebooks/          # Jupyter 실습 파일
└── 03-python-basics.md
```

{% hint style="warning" %}
`.venv`는 실행 환경에 따라 내용이 달라지므로 다른 사람에게 복사하거나 Git에 커밋하지 않는다. 다른 환경에서는 `requirements.txt`를 사용해 새로 만든다.
{% endhint %}

## 2.2 실습 파일 준비하기

GitBook은 교안을 읽는 화면이며, 터미널 실습에는 저장소 파일이 필요하다. Git이 설치돼 있다면 다음 명령으로 저장소를 내려받고 프로젝트 루트로 이동한다.

```bash
git clone https://github.com/zxz3650/Python.git
cd Python
```

Git을 사용하지 않는다면 [GitHub 저장소](https://github.com/zxz3650/Python)에서 **Code → Download ZIP**을 선택하고 압축을 푼다. 이후 터미널이나 PowerShell에서 압축을 푼 폴더로 이동한다.

이후 명령은 다음 두 파일이 보이는 프로젝트 루트에서 실행한다.

- [requirements.txt](requirements.txt): 핵심 과정 패키지 목록
- [notebooks/README.md](notebooks/README.md): Notebook 실습 안내

저장소를 clone한 폴더는 보통 `Python`이고 ZIP 파일을 푼 폴더는 `Python-master`일 수 있다. 이 장에서 말하는 **프로젝트 루트**는 폴더 이름과 관계없이 `requirements.txt`와 `notebooks`가 함께 있는 위치다.

## 2.3 Python 설치와 버전 확인

`venv` 경로를 선택했다면 현재 설치된 버전을 먼저 확인한다. 결과가 `3.10` 이상이면 바로 2.4절로 이동할 수 있다. 새로 설치하거나 여러 버전 중 하나를 선택할 수 있다면 Python 3.12를 사용한다. conda 경로를 선택했다면 이 절을 건너뛰고 2.5절로 이동한다.

### Windows

1. [Python 공식 다운로드 페이지](https://www.python.org/downloads/)에서 Python 3.12 설치 프로그램을 내려받는다.
2. 설치 화면에 `Add python.exe to PATH` 선택지가 있으면 활성화한다.
3. 새 PowerShell 또는 명령 프롬프트를 열어 버전을 확인한다.

```powershell
py -3.12 --version
py -0p
```

`py` 명령을 사용할 수 없다면 다음 명령을 확인한다.

```powershell
python --version
```

`python`이나 `py`를 찾을 수 없다면 기존 터미널을 닫고 새로 연다. 그래도 찾지 못하면 설치 프로그램을 다시 실행해 Python Launcher와 PATH 설정을 확인한다.

### macOS

macOS에 포함된 Python과 과정용 Python을 구분한다. [Python 공식 설치 프로그램](https://www.python.org/downloads/)을 사용하거나 Homebrew가 이미 설치돼 있다면 다음과 같이 Python 3.12를 설치한다.

```bash
brew install python@3.12
python3.12 --version
```

이후 가상환경을 만들 때도 `python3.12`를 사용한다. 설치 출처가 다른 `python3`와 `pip3` 명령을 임의로 섞지 않는다.

### Linux

배포판에 설치된 버전을 먼저 확인한다.

```bash
python3 --version
```

Debian·Ubuntu·Kali 계열에서 Python과 `venv`가 없다면 다음 패키지를 설치한다.

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Fedora 계열과 Arch 계열의 대표 명령은 다음과 같다. 배포판 버전에 따라 패키지 이름이 다를 수 있으므로 설치 전 공식 문서를 함께 확인한다.

```bash
# Fedora 계열
sudo dnf install -y python3 python3-pip

# Arch 계열
sudo pacman -S python python-pip
```

{% hint style="warning" %}
Linux의 시스템 Python에 `sudo pip install ...`로 패키지를 설치하지 않는다. 운영체제 도구가 사용하는 패키지와 충돌할 수 있으므로 과정 패키지는 다음 절의 가상환경 안에 설치한다.
{% endhint %}

## 2.4 `venv` 가상환경 만들기

가상환경은 프로젝트마다 독립된 Python 실행 파일과 패키지 설치 위치를 제공한다. 아래 명령은 2.2절에서 확인한 프로젝트 루트에서 실행한다.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip --version
```

Python 3.10 또는 3.11을 계속 사용한다면 `py -0p`로 설치 경로를 확인하고 `-3.12`를 실제 버전(예: `-3.11`)으로 바꾼다.

PowerShell에서 스크립트 실행이 차단되면 정책을 영구 변경하기 전에 명령 프롬프트에서 다음 활성화 파일을 사용할 수 있다.

```bat
.venv\Scripts\activate.bat
```

### macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
python -m pip --version
```

앞 절에서 확인한 `python3`가 이미 3.10 이상이라면 첫 명령을 `python3 -m venv .venv`로 바꿀 수 있다.

### Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
python -m pip --version
```

활성화에 성공하면 터미널 프롬프트 앞에 보통 `(.venv)`가 표시된다. 프롬프트만 믿지 말고 실제 실행 파일도 확인한다.

```bash
python -c "import sys; print(sys.executable)"
```

출력 경로에 `.venv`가 포함돼야 한다. 실습을 마친 뒤에는 다음 명령으로 가상환경을 비활성화한다.

```bash
deactivate
```

### 가상환경이 격리를 만드는 이유

가상환경을 활성화하면 터미널의 `PATH` 앞부분에 `.venv`의 실행 파일 경로가 추가된다. 이후 `python`과 `python -m pip`는 같은 가상환경을 가리킨다. 프로젝트마다 서로 다른 패키지 버전을 사용해도 시스템 Python이나 다른 프로젝트에 영향을 주지 않는다.

## 2.5 선택 경로: Miniconda

이미 conda를 사용하거나 별도의 conda 환경이 필요한 학습자만 이 경로를 선택한다. `venv`와 conda 환경을 동시에 활성화하지 않는다.

conda 명령을 사용할 수 있어야 한다. 아직 설치하지 않았다면 [Miniconda 설치 안내](https://www.anaconda.com/docs/getting-started/miniconda/install)를 먼저 따른다. 설치가 끝나면 다음 명령으로 환경을 만든다.

```bash
conda create -n python-basic python=3.12 pip -y
conda activate python-basic
python --version
python -m pip --version
```

환경 목록과 현재 활성화된 환경을 확인한다.

```bash
conda env list
```

2.6절로 계속 진행할 때는 `python-basic` 환경을 활성화한 상태로 유지한다. 과정 실습을 모두 마친 뒤에는 다음 명령으로 비활성화한다.

```bash
conda deactivate
```

이 과정의 의존성 기준은 `requirements.txt`이므로 같은 환경에서 `conda install`과 `pip install`을 임의로 반복하지 않는다. conda 전용 환경 파일을 별도로 관리하는 프로젝트라면 그 프로젝트의 설치 지침을 우선한다.

## 2.6 과정 패키지 설치하기

2.4절의 `.venv` 또는 2.5절의 conda 환경을 활성화한 상태에서 저장소의 `requirements.txt`를 사용한다.

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

핵심 요구사항에는 다음 패키지가 포함된다.

| 패키지 | 사용하는 과정 |
| --- | --- |
| `pytest` | 09장 테스트 |
| `numpy`, `pandas` | 05장 데이터 분석 |
| `requests` | 07장 HTTP와 08장 자동화 |
| `jupyterlab`, `ipykernel` | Notebook 실습 |

`pip` 대신 `python -m pip`를 사용하면 현재 `python`과 연결된 pip를 명시적으로 실행할 수 있다. 설치가 끝난 뒤 두 경로를 다시 확인한다.

```bash
python -c "import sys; print(sys.executable)"
python -m pip --version
```

{% hint style="info" %}
Beautiful Soup, Scapy, pwntools, PyCryptodome 같은 패키지는 핵심 환경에 미리 설치하지 않는다. 해당 패키지를 사용하는 보충·심화 실습에서 정확한 배포 패키지 이름과 플랫폼 조건을 확인한 뒤 추가한다.
{% endhint %}

## 2.7 JupyterLab과 커널 확인

Jupyter 커널은 Notebook 셀의 Python 코드를 실제로 실행하는 프로세스와 환경이다. 앞에서 선택한 가상환경을 활성화한 터미널에서 JupyterLab을 실행한다.

```bash
jupyter lab
```

여러 가상환경을 Jupyter에서 구분해야 할 때만 현재 환경을 커널로 등록한다.

```bash
python -m ipykernel install --user --name python-basic --display-name "Python (python-basic)"
```

Notebook의 첫 셀에서 실제 커널을 확인한다.

```python
import sys

print(sys.executable)
print(sys.version)

assert sys.version_info >= (3, 10)
```

`sys.executable`이 앞에서 선택한 환경을 가리켜야 한다. `venv` 경로라면 `.venv`가, conda 경로라면 `python-basic` 환경의 디렉터리가 출력에 포함된다. 다른 경로가 출력되면 Jupyter의 커널 선택 메뉴에서 `Python (python-basic)`을 선택한다.

{% hint style="warning" %}
터미널에서 패키지를 설치했는데 Notebook에서 `ModuleNotFoundError`가 발생하면 설치 실패보다 **터미널의 Python과 Notebook 커널이 다른 경우**를 먼저 확인한다.
{% endhint %}

## 2.8 설치 결과 검증하기

다음 코드를 `verify_setup.py`로 저장하고 가상환경에서 실행한다.

```python
from __future__ import annotations

import importlib.util
import sys


REQUIRED_MODULES = {
    "pytest": "pytest",
    "numpy": "numpy",
    "pandas": "pandas",
    "requests": "requests",
    "jupyterlab": "jupyterlab",
    "ipykernel": "ipykernel",
}


print(f"Python: {sys.version.split()[0]}")
print(f"Executable: {sys.executable}")

if sys.version_info < (3, 10):
    print("[FAIL] Python 3.10 이상이 필요하다.")
    raise SystemExit(1)

missing = []
for distribution, module_name in REQUIRED_MODULES.items():
    if importlib.util.find_spec(module_name) is None:
        print(f"[MISSING] {distribution}")
        missing.append(distribution)
    else:
        print(f"[OK] {distribution}")

if missing:
    print("다음 패키지를 requirements.txt로 다시 설치한다:")
    print(", ".join(missing))
    raise SystemExit(1)

print("[OK] 실습 환경 검증 완료")
```

```bash
python verify_setup.py
```

검증이 실패하면 누락된 패키지만 임의로 설치하기 전에 다음 명령을 다시 실행한다.

```bash
python -m pip install -r requirements.txt
```

## 2.9 문제 해결 순서

환경 문제가 생기면 패키지를 반복해서 다시 설치하기보다 아래 순서로 경로를 확인한다.

| 증상 | 먼저 확인할 것 | 해결 방향 |
| --- | --- | --- |
| `python` 또는 `py`를 찾지 못함 | 새 터미널에서도 같은지 확인 | Python 설치와 PATH·Launcher 설정을 확인한다. |
| `venv` 생성 실패 | Python 버전과 `python3-venv` 설치 여부 | 올바른 Python으로 다시 생성한다. |
| `ModuleNotFoundError` | `sys.executable`, `python -m pip --version` | 같은 가상환경을 가리키게 한다. |
| Notebook에서만 import 실패 | Notebook의 `sys.executable` | 올바른 커널을 선택한다. |
| Linux에서 `externally-managed-environment` 오류 | 시스템 Python에 설치 중인지 확인 | `.venv`를 활성화한 뒤 설치한다. |
| 패키지 설치 중 컴파일 오류 | 운영체제, Python 버전, wheel 제공 여부 | 해당 패키지의 공식 설치 조건을 확인한다. |

오류 메시지는 마지막 한 줄만 보지 않는다. 실행한 명령, 사용한 Python 경로, 오류 유형과 처음 실패한 지점을 함께 기록하면 다른 사람이 같은 문제를 재현하기 쉽다.

## 2.10 직접 해보기

다음 순서로 환경이 실제로 분리되는지 확인한다.

1. 선택한 `.venv` 또는 conda의 `python-basic` 환경을 활성화하고 `sys.executable`을 확인한다.
2. `python -m pip --version`이 같은 환경의 경로를 가리키는지 확인한다.
3. `verify_setup.py`를 실행해 모든 항목이 `[OK]`인지 확인한다.
4. JupyterLab에서 Notebook을 열고 같은 `sys.executable`이 출력되는지 확인한다.
5. `deactivate` 또는 `conda deactivate` 후 Python 경로가 달라지는지 비교한다.

### 응용 인사이트: 환경 정보도 재현 가능한 결과의 일부다

같은 코드라도 Python과 패키지 버전이 다르면 출력이나 오류가 달라질 수 있다. 문제를 공유할 때는 코드만 전달하지 않고 다음 정보도 함께 기록한다.

```bash
python --version
python -m pip --version
python -m pip freeze
```

`pip freeze` 결과에는 직접 설치하지 않은 하위 의존성이나 내부 패키지 이름·다운로드 위치가 포함될 수 있다. 외부에 공유하기 전에 내용을 확인한다. 저장소의 공식 설치 기준은 `requirements.txt`이며, `pip freeze`는 현재 환경을 조사하고 문제를 재현할 때 참고 자료로 사용한다.

## 완료 기준

- [ ] Python 3.10 이상을 실행할 수 있다.
- [ ] 교안 저장소의 `.venv` 또는 conda의 `python-basic` 환경을 만들고 활성화할 수 있다.
- [ ] `python`과 `python -m pip`가 같은 가상환경을 가리키는지 확인할 수 있다.
- [ ] `requirements.txt`의 패키지를 설치할 수 있다.
- [ ] JupyterLab에서 올바른 커널을 선택할 수 있다.
- [ ] `verify_setup.py`로 Python 버전과 핵심 패키지를 검증할 수 있다.
- [ ] 환경 오류가 발생했을 때 Python·pip·커널 경로를 순서대로 확인할 수 있다.

## 공식 참고 문서

- [Python 다운로드](https://www.python.org/downloads/)
- [Python Packaging User Guide: pip와 가상환경](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)
- [IPython: Jupyter 커널 설치](https://ipython.readthedocs.io/en/stable/install/kernel_install.html)
- [Conda: 환경 관리](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html)
- [Homebrew: Python 3.12](https://formulae.brew.sh/formula/python@3.12)

---

다음 장: [03. Python 기초 문법](03-python-basics.md)
