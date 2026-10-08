# 프로야구 스피리츠 6 PS2 한글패치

PS2 일본판 **プロ野球スピリッツ6 (Pro Yakyuu Spirits 6, SLPM-55158)** 용 비공식 한국어 패치입니다. 메뉴·도움말·이벤트 대사·선수 이름·이미지 글자를 한글화했습니다. 현재 배포판은 **v1.0 (2026-10-03)** 입니다.

[패치 다운로드](https://github.com/snake759494/pro-yakyuu-spirits-6-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 **ProYakyuuSpirits6_PS2_KO_v1.0.xdelta 하나**입니다. 저장소에는 제작 도구·번역 대역표·검증 자료를 공개합니다. 원본 및 완성 ISO, 추출된 게임 바이너리·이미지·음성·영상, 글꼴 파일, 외부 실행 파일은 포함하지 않습니다.

> `translation/`에는 대사와 선수 소개 등 번역 대역표가 있으므로 **스포일러**가 포함됩니다.
> 최종 ISO의 부팅·페넌트 화면과 앞선 빌드의 WBC 한일전 실행을 확인했습니다. 전체 경기·시즌·이벤트 분기를 완주한 검수판은 아닙니다. 빌드별 확인 범위는 [실행 검증 기록](validation/runtime_verification.json)에 구분했습니다.

## 대상 버전

수정되지 않은 **PS2 일본판 SLPM-55158 DVD ISO (2,048바이트 섹터)** 에 적용합니다. 파일명보다 크기와 해시가 일치하는지가 중요합니다.

| 항목 | 값 |
| --- | --- |
| 게임 ID | SLPM-55158 |
| 원본 ISO 크기 | 4,424,990,720 바이트 |
| **원본 ISO MD5** | `3c879d2082b2406dae1bfb71eab9b6d7` |
| 원본 ISO SHA-1 | `607c5e9b3cc65e6dc8336c8589c11b8768348575` |
| 원본 ISO SHA-256 | `51bfd7a40f1855470ce3bcb467102cf535707ba1d5d1f1d5b23d4d2c1aab8559` |
| xdelta 크기 | 3,553,272 바이트 |
| xdelta SHA-256 | `9f03db6a17077a22e0e2cd35bbd18dda3b0a543909ea38fbc669a11d92f9c6c0` |
| 결과 ISO 크기 | 4,424,990,720 바이트 |
| 결과 ISO SHA-1 | `a14deaa8d55ebde33cd53a3046dba6ed859fdde0` |
| 결과 ISO SHA-256 | `5b7a4c5788ac197276e1c1f1a0222a2d3e94e6a4bad261e652a0ac10eea4daa4` |

## 패치 적용 방법

### 원본 확인 (Windows)

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\Pro Yakyuu Spirits 6 (Japan).iso'
```

위 표와 다르면 적용하지 마세요. 다른 지역판이나 CHD·CSO 형식에는 직접 적용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `ProYakyuuSpirits6_PS2_KO_v1.0.xdelta`를 받습니다.
2. xdelta3 패치를 지원하는 도구의 **Apply Patch**를 엽니다.
3. **Patch**에 xdelta, **Source File**에 해시가 일치하는 원본 ISO를 선택합니다.
4. **Output File**에 원본과 같은 폴더의 `Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso`를 지정합니다. 원본을 덮어쓰지 마세요.

기존 게임 패치와 동일하게 2차 압축과 파일 경로 헤더 없이 만들었습니다. xdelta는 [공식 프로젝트](https://github.com/jmacd/xdelta)를 참고하세요.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\Pro Yakyuu Spirits 6 (Japan).iso' '.\ProYakyuuSpirits6_PS2_KO_v1.0.xdelta' '.\Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
```

해시 자동 검사 적용기(Python 3 + xdelta3, 기존 출력 파일 덮어쓰기 금지):

```powershell
python tools/apply_release.py --xdelta .\xdelta3.exe --source '.\Pro Yakyuu Spirits 6 (Japan).iso' --patch .\ProYakyuuSpirits6_PS2_KO_v1.0.xdelta --output '.\Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso'
```

### PCSX2에서 실행

한글판 ISO를 **새로 부팅**하세요. 이전 버전 세이브스테이트 대신 게임 내 메모리카드 저장을 사용하세요. 실기 실행 검증은 하지 않았습니다.

## 작업 내용과 범위

| 구분 | 내용 |
| --- | --- |
| 일반 UI | 최종 ISO 문자열 13,103개 위치 읽기 검증 |
| 선수·감독 | 1,276명; 메이저리그 2009 참고 프로젝트 일치 385명, NPB 공식 독음 686명, 등록명·외국인 표기 검수 205명 |
| WBC | 선수 ID에 연결한 별도 표시 이름 448개; 한국·일본 대표팀 명단 확인 |
| 이벤트·안내 | 육성 대사 1,570종, WBC 이벤트 26종, 로딩 팁 90개, 응원 문구 300개 |
| 글꼴 | 나눔스퀘어 네오 Bold, 감사된 미사용 슬롯 1,268개 사용 |
| 이미지 | 기본 메뉴 이미지에 추가한 모드별 아틀라스 584개 |
| 최종 품질 개선 | 336개 이미지의 867개 영역 검사, 페넌트 제목·팀명·순위·흐르는 안내문 수정 |

선수 이름 검수에는 [실황 파워풀 메이저리그 2009 프로젝트](https://github.com/snake759494/jikkyou-powerful-major-league-2009-korean-patch)와 NPB 공식 독음을 참고했습니다. 게임 간 바이너리 구조를 직접 이식하지 않았습니다.

## 검증과 알려진 한계

- 전체 FBD 리소스 4,441개 및 실행 파일 읽기 검증, 원본 ISO 보존 확인.
- UI 13,103곳, 선수·감독 1,276명, WBC 표시 이름 448개, 응원 문구 300개의 적용 불일치 0건.
- 추가 검수 이미지 336개의 내용·헤더·번역 영역 밖 픽셀 보존 검사 통과.
- xdelta를 원본 ISO에 적용한 결과의 크기와 MD5·SHA-1·SHA-256이 최종 ISO와 일치.
- 최종 ISO: 부팅, 일반 메뉴, 페넌트 소개·설정·개막 안내·메인 화면 확인. 앞선 빌드: WBC 한국·일본 명단, 한일전 타석·소개·타임 메뉴 확인.
- 전체 시즌·모든 이벤트 분기·경기 완주 및 실기 검수는 미완료입니다. 테스트용 메모리카드 공간 부족으로 페넌트 저장·불러오기 검증은 완료하지 못했습니다.
- 일본어 음성, 공식 로고·유니폼·구장 광고·제작진 크레딧은 유지합니다. 이름 발음용 가나·음성 키, 한자 변환 사전, 선수 암호 문자 배열도 호환성을 위해 보존합니다.

## 저장소 구성

| 경로 | 내용 |
| --- | --- |
| `tools/` | 적용·빌드·폰트·아카이브·텍스처 처리 도구 |
| `translation/` | 번역 결과, 원문 매핑·오프셋 (스포일러) |
| `metadata/` | 재빌드에 필요한 문자 슬롯·검수 위치·추출 목록 |
| `validation/` | 빌드·문자열·이미지·실행 검증 기록 |
| `docs/` | 기술 설명·재빌드 절차·글꼴 출처 |
| `release_manifest.json` | 배포 파일과 원본·결과 해시 |

오역·잘림 신고에는 모드, 화면 위치, 스크린샷, 패치 버전과 새 부팅 여부를 함께 남겨 주세요.


## PCSX2 16:9 와이드 패치

각 릴리즈에 와이드 `.pnach` 파일을 함께 제공합니다. [설치·활성화·해제 방법](docs/WIDESCREEN.md)을 참고하세요.
