# Python 가상환경 설정방법



### 가상환경 생성

> `venv`라는 이름의 가상환경을 생성합니다. 현재 파이썬 버전의 가상환경이 생성됩니다.

```shell
$ python -m venv venv
```



### 가상환경 실행

> `venv` 안에 `Scripts` 안에 `actibate.bat` 파일을 실행합니다.

```shell
$ venv/Scripts/activate.bat
```



### 라이브러리 설치

> `requirement.txt`에 어떤 라이브러리들이 필요한지 적혀있습니다. 해당 라이브러리를 한번에 다운받을 수 있습니다.

```shell
$ pip install -r requirement.txt
```



### 설치된 라이브러리 기록 남기기

> 본인이 새로운 라이브러리를 추가했다면 해당 기록 `requirement.txt`에 남길 수 있습니다. 

```shell
$ pip freeze > requirement.txt
```



### 가상환경 종료

> `venv` 가상환경을 종료합니다.

```shell
$ deactivate venv
```



