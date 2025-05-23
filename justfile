default:
    @just --dump

build:
    zip -r build.zip webchef-v2
    mv build.zip builds/build-$(date +%Y-%m-%d_%H-%M-%S).zip

_build-legacy:
    zip -r build-legacy.zip webchef-v1
    mv build-legacy.zip archive/builds/build-$(date +%Y-%m-%d_%H-%M-%S).zip

format:
    prettier --write .

push:
    git add .
    -git commit -m "$(date '+%Y-%m-%d %H:%M')"
    -git push origin main
