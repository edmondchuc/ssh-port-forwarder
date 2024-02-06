#!/bin/sh

APP_NAME="SSH Port Forwarder"

mkdir -p dist/dmg
rm -r dist/dmg/*
cp -r "dist/${APP_NAME}.app" dist/dmg
test -f "dist/${APP_NAME}.dmg" && rm "dist/${APP_NAME}.dmg"
create-dmg \
  --volname "${APP_NAME}" \
  --volicon "img/icon.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 175 120 \
  --hide-extension "${APP_NAME}.app" \
  --app-drop-link 425 120 \
  "dist/${APP_NAME}.dmg" \
  "dist/dmg/"