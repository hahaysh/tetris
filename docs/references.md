# 참고 프로젝트 조사

구현에 앞서 브라우저 낙하 블록 프로젝트와 Python 웹 runtime 선택지를 소스 수준에서
검토했습니다. GitHub의 `pushed_at` 값에는 코드와 무관한 branch 갱신이 포함될 수 있으므로
활동성은 기본 branch의 commit을 기준으로 판단했습니다. License 정보는 조사 당시 upstream
저장소 상태를 설명하며 실제 재사용 전에는 다시 확인해야 합니다.

아래 프로젝트의 소스 코드, 그림, 소리, 이름, branding은 복사하지 않았습니다. Stackline은
일반적인 게임 mechanic과 architecture pattern을 참고해 새로 구현했습니다.

## 비교 저장소

| 프로젝트 | 검증한 가치 | 제약 | Stackline에 반영한 방식 |
| --- | --- | --- | --- |
| [simonlc/tetr.js](https://github.com/simonlc/tetr.js) | SRS, 7-bag, lock delay, DAS/ARR, hold, ghost, seed replay | MIT, 자동화 테스트 없음, 오래된 기본 branch, 전역 상태 및 sort 기반 shuffle | 규칙 checklist와 결정론적 replay 목표만 채택하고 알고리즘은 Python으로 새로 구현해 테스트 |
| [mimshwright/mimstris](https://github.com/mimshwright/mimstris) | Matrix utility, 분리된 상태 관심사, AVA 테스트 | MIT, 7-bag/hold/ghost/lock delay 없음, 2022년 이후 비활성 | 작은 도메인 module과 행위 중심 테스트 구성 |
| [eniompw/Vibe-Tetris-Pygame-Web](https://github.com/eniompw/Vibe-Tetris-Pygame-Web) | 비동기 pygame loop 및 pygbag 배포 사례 | MIT, 단일 파일 설계, 테스트 없음, 균등 난수와 비-SRS kick | 웹 packaging 가능성만 확인하고 단일 구조와 규칙은 채택하지 않음 |
| [ovidiuch/flatris](https://github.com/ovidiuch/flatris) | 공유 reducer, 의도 중심 action, action chain, 재연결 backfill | MIT, 오래된 Next/React/Socket.IO stack, 최근 기본 branch 개발 없음 | 향후 multiplayer 참고 자료로만 사용하고 MVP 의존성에서는 제외 |
| [chvin/react-tetris](https://github.com/chvin/react-tetris) | 터치 UI, 제어된 입력 반복, focus pause, 상태 복원, 오디오 UX | Package metadata는 Apache-2.0을 선언하지만 저장소에 license 본문이 없고 framework가 오래됨 | UX 동작만 관찰하고 코드와 asset은 재사용하지 않음 |
| [zishankadri/tetris-bugs](https://github.com/zishankadri/tetris-bugs) | PyScript/Flask 통합 및 여러 application mode | 일반적인 규칙 참고용이 아닌 특수 coding game | PyScript 및 서버 조합 대안의 근거 |
| [arassp/Tetris](https://github.com/arassp/Tetris) | 최소 Python 브라우저 canvas 사례와 GitHub Pages 배포 | 균등 난수를 사용하는 교육용 단일 구조 | 배포 방식 비교에만 사용 |

## 기술 선택

실용적인 Python 중심 접근법 세 가지를 비교했습니다.

### pygame-ce와 pygbag

MVP에 선택한 stack입니다. Python이 규칙, 입력 처리, 렌더링, 오디오를 소유하고 pygbag이
CPython WebAssembly와 정적 packaging을 제공합니다. 하나의 client 코드 경로, 네이티브
pytest 검증, 직접적인 터치 지원, 정적 hosting이 장점입니다. 초기 runtime download가 크고
비동기 loop 제약과 version에 민감한 packaging 동작이 있다는 tradeoff가 있습니다.

공식 자료:

- [pygame-ce](https://github.com/pygame-community/pygame-ce)
- [pygbag](https://github.com/pygame-web/pygbag)
- [pygame-web 문서](https://pygame-web.github.io/wiki/pygbag/)

### PyScript 또는 Pyodide와 JavaScript canvas shell

규칙은 Python에 유지하지만 렌더링, 입력, 오디오를 JavaScript나 TypeScript로 분리하는
방식입니다. DOM과 접근성 측면에서 더 유연하지만 interop 계층, 두 개의 테스트 표면, 추가
통합 코드가 필요해 canvas 중심인 이 게임에는 복잡도가 더 큽니다.

공식 자료:

- [PyScript](https://pyscript.net/)
- [Pyodide](https://pyodide.org/)

### Python backend와 TypeScript client

계정, 권위 있는 점수, multiplayer가 핵심 요구사항이라면 FastAPI와 브라우저 네이티브
client 조합이 적합합니다. 그러나 이 방식은 Python을 로컬 게임 runtime으로 사용하지 않으며
offline single-player MVP에는 이점 없이 배포, 지연, protocol, 운영 비용을 추가합니다.
따라서 backend는 선행 조건이 아니라 향후 추가 가능한 경계로 남겨 둡니다.

공식 자료: [FastAPI](https://fastapi.tiangolo.com/)

## 채택한 Pattern

- 규칙을 렌더링과 독립된 결정론적 도메인으로 취급
- seed 기반 Fisher-Yates 7-bag 및 table 기반 SRS 전이 사용
- Host 키 반복 대신 애플리케이션 코드에서 DAS/ARR 생성
- 키보드와 터치를 하나의 command model로 전달
- 브라우저 통합 전에 상태 전이 경계에서 mechanic 테스트
- 초기 release는 정적으로 유지하고 기능이 요구할 때까지 network 권한을 연기

## 제외한 Pattern

- 무제한 piece drought를 허용하는 균등 난수 선택
- 제한된 lock delay 없이 첫 접촉 즉시 block 고정
- 규칙, timing, 렌더링, 입력, 배포 관심사를 한 module에 결합
- License 조건이 없거나 모호한 저장소의 코드 또는 asset 복사
- Web app이라는 이름만을 위해 backend나 WebSocket 추가
