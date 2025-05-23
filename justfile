default:
    @just --dump

build:
    zip -r webchef-script.zip webchef-script
    mv webchef-script.zip archive/builds/build-$(date +%Y%m%d%H%M%S).zip
    just push

format:
    prettier --write .

push:
    git add .
    -git commit -m "$(date '+%Y-%m-%d %H:%M')"
    -git push origin main
