[app]

title = Food Options
package.name = foodoptions
package.domain = org.winston310

source.dir = .
source.include_exts = py,kv,json,png,jpg,atlas

version = 0.1

requirements = python3,kivy,android

orientation = portrait
fullscreen = 0

android.permissions = CAMERA
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a


[buildozer]

log_level = 2
warn_on_root = 1
