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

# Open the Meter tab and capture it.
for n in nodes():
    if (n.get("text") or "").strip() == "Meter" or (n.get("content-desc") or "").strip() == "Meter":
        x1, y1, x2, y2 = map(int, __import__("re").findall(r"\d+", n["bounds"]))
        adb("shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2))
        break
time.sleep(1.5)
shot("journey-meter")

print(f"smoke ok: WebView on screen, map-fit.png {size} bytes")
