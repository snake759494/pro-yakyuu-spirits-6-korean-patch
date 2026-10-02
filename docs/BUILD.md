# 재빌드

Python 3.13에서 제작했습니다. 루트에 해시가 일치하는 원본 `Pro Yakyuu Spirits 6 (Japan).iso`와 `NanumSquareNeo-cBd.ttf`를 준비합니다. 원본 및 글꼴은 저장소에 없습니다.

```powershell
python -m pip install -r requirements.txt
python tools/prepare_release_build.py
python tools/build.py --check
python tools/build.py
python tools/verify_built_text.py
python tools/verify_picture_patch.py
python tools/coverage_report.py
```

출력은 원본 옆의 `Pro Yakyuu Spirits 6 (Japan) (Korean DEV).iso`입니다. 실제 빌드는 이 고정 출력 파일을 갱신하므로 사용 중인 에뮬레이터를 종료하세요. `--check`는 ISO를 쓰지 않습니다. 출력 검증 해시는 release_manifest.json과 비교합니다.

prepare_release_build.py는 원본 해시를 확인한 뒤 필요한 ELF·OVL·CHK를 개인 work/ 폴더에 추출하고 metadata/를 복사합니다. 생성된 바이너리는 Git에서 제외됩니다. 검수된 글꼴 슬롯과 문자 위치 메타데이터를 재사용하며 네트워크에서 이름을 재수집할 필요는 없습니다.

번역을 수정한 경우 해당 컴파일러를 실행합니다: overlay_*.txt는 `python tools/overlay_texts.py`, events_*.txt는 `python tools/event_texts.py`. 줄 수·서식 명령·용량 검사를 통과한 뒤 빌드하세요. 검증된 슬롯 1,268개가 모두 사용되므로 새 음절을 추가할 때 글꼴 공간부터 확인해야 합니다.

`python tools/build.py --check --verify-existing`는 소스에서 재생성한 실행 파일과 모든 FBD 항목을 기존 ISO와 대조합니다. 번역 소스가 바뀌면 다시 실행 검증해야 합니다. tools/에는 개발 중 분석 도구도 들어 있으며, 재빌드는 위 순서만으로 진행합니다.

OpenCV/Pillow 및 글꼴 버전에 따라 그림 래스터 결과가 달라질 수 있습니다. 배포 패치의 기준은 release_manifest.json의 결과 해시입니다.
