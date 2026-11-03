[app]

title = JARVIS AI
package.name = jarvisai
package.domain = org.deepak
source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 1.0

requirements = python3,kivy,plyer,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,RECORD_AUDIO

android.api = 35
android.minapi = 24

android.archs = arm64-v8a

[buildozer]

log_level = 2
warn_on_root = 1
