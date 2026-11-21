"""Emulator smoke for tuju: launches the app and verifies the map WebView renders."""
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PKG = "com.vanipy.tuju"
OUT = "ci/shots"
subprocess.run(["mkdir", "-p", OUT])


def adb(*a):
    return subprocess.run(["adb", *a], capture_output=True)


def shot(name):
    time.sleep(1.0)
    data = adb("exec-out", "screencap", "-p").stdout
    path = f"{OUT}/{name}.png"
    open(path, "wb").write(data)
    return len(data)


def nodes():
    last = ""
    for _ in range(5):
        adb("shell", "rm", "-f", "/sdcard/ui.xml")
        dump = adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        raw = adb("exec-out", "cat", "/sdcard/ui.xml")
        xml = raw.stdout.decode("utf-8", "replace")
        try:
            if dump.returncode or raw.returncode:
                raise ET.ParseError("UI dump command failed")
            return [n.attrib for n in ET.fromstring(xml).iter("node")]
        except ET.ParseError:
            last = repr(xml) + "\n" + dump.stdout.decode("utf-8", "replace") + dump.stderr.decode("utf-8", "replace")
            time.sleep(1)
    open(f"{OUT}/ui-dump-failure.txt", "w").write(last)
    shot("FAILED-ui-dump")
    raise RuntimeError("No valid UIAutomator XML after five attempts; raw diagnostic saved")


adb("shell", "am", "start", "-n", f"{PKG}/.MainActivity")
time.sleep(4)

ns = nodes()
if not any("WebView" in (n.get("class") or "") for n in ns):
    shot("FAILED-no-webview")
    sys.exit("no WebView found on screen after launching the app")

size = shot("map-fit")
if size < 20000:
    sys.exit(f"screenshot suspiciously small ({size} bytes); map may not have rendered")

# Scroll down to the journey meter and capture it too.
for _ in range(4):
    adb("shell", "input", "swipe", "540", "1800", "540", "500", "300")
    time.sleep(0.6)
shot("journey-meter")

# Keep scrolling to the bottom: the IDSW access guideline card is the last
# element on the page. Extra swipes past the end are harmless.
for _ in range(6):
    adb("shell", "input", "swipe", "540", "1800", "540", "500", "300")
    time.sleep(0.6)
shot("access-guideline")

print(f"smoke ok: WebView on screen, map-fit.png {size} bytes")
