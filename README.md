# 과제2 · 에이전트와 함께 만드는 URL 단축기

2026-2 **고급알고리즘**(SIT2001-01) 과제2의 **시작 저장소**입니다.
채팅창에 묻고 복사·붙여넣기 하던 방식에서 벗어나, Codespace 안의 에이전트가
저장소를 읽고, 파일을 고치고, 테스트를 직접 돌리게 하는 방법을 익힙니다.

- 과제 안내: [lec-algorithm.github.io/lecture/article/hw2-2026](https://lec-algorithm.github.io/lecture/article/hw2-2026/)
- 수업 슬라이드: [lec-algorithm.github.io/lecture/slides/hw2-2026](https://lec-algorithm.github.io/lecture/slides/hw2-2026/)
- 해시 테이블 복습: [주제 08 해시 테이블](https://lec-algorithm.github.io/lecture/course/topic-08-hashing/)

## 시작하기

1. 이 저장소 상단의 **Use this template** → **Create a new repository**
2. 저장소 이름은 `algorithms-hw2`처럼 정합니다. 공개(Public)로 만듭니다.
3. 만들어진 **내 저장소**에서 **Code** → **Codespaces** 탭 → **Create codespace on main**
4. 왼쪽 막대의 Copilot 아이콘을 눌러 채팅 창을 열고, 창 아래쪽에서 **Agent** 모드를 고릅니다.

## 들어 있는 것

| 파일 | 하는 일 |
| --- | --- |
| `SPEC.md` | URL 단축기, 해시 테이블, 경계 사례의 명세 |
| `src/` · `tests/` | base62, 해시 테이블, 단축기와 웹 서버 및 테스트 |
| `experiments/` | 적재율에 따른 탐색 비용 CSV, SVG, PDF 보고서 |
| `tools/catchup.sh` | 수업 중 놓친 단계를 따라잡는 스크립트 |
| `Makefile` | `make test` · `make serve` · `make experiment` · `make compare` |

## 명령

컨테이너 안(Codespaces 터미널)에서 실행합니다.

| 하고 싶은 것 | 명령 |
| --- | --- |
| 테스트 | `make test` |
| 웹 서버 (포트 8000) | `make serve` (기본 선형 탐지; 입력 폼에서도 방식 선택 가능) |
| 충돌 실험 | `make experiment` |
| 두 해시 테이블 비교 | `make compare` |
| 놓친 단계 따라잡기 | `sh tools/catchup.sh <단계 번호>` |

`make experiment`는 고정된 4093개 버킷에 무작위 URL을 넣어 측정하고,
`experiments/results.csv`와 `experiments/results.svg`를 갱신합니다.
Codespaces에서 휴대폰으로
서버를 확인할 때는 포트 8000을 Public으로 설정하고, 확인을 마치면 서버를 끄고
포트를 Private으로 되돌립니다.

`make compare`는 연결 리스트와 선형 탐지를 같은 키로 비교해
`experiments/table_comparison.csv`, `experiments/table_comparison.svg`,
`experiments/table_comparison_report.pdf`(2쪽)를 생성합니다.

웹 서버가 만든 URL 매핑은 `data/urls.csv`에 저장되어 서버를 다시 시작하거나
충돌 처리 방식을 바꿔도 유지됩니다. 입력 폼과 `/table`에서 개별 체이닝/선형 탐지를
각각 선택할 수 있고, 결과에도 사용한 방식을 표시합니다. 이 사용자 데이터 파일은
Git에 커밋되지 않습니다.

외부 라이브러리는 쓰지 않습니다. Python 표준 모듈만으로 충분합니다.

## 로컬에서 하기

```sh
git clone https://github.com/<본인 계정>/<내 저장소>.git
cd <내 저장소>
docker compose up -d
docker compose exec lab bash
```

**이후 모든 `docker compose` 명령은 이 폴더에서 칩니다.**
