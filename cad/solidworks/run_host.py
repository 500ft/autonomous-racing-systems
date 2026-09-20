#!/usr/bin/env python3
"""Run a host-side SOLIDWORKS authoring script inside the host's interactive session.

Workstation side. Uploads the script plus its inputs, launches it through PsExec
into the logged-in session (SOLIDWORKS' COM server will not start from a plain SSH
session), polls for the result file, and retrieves it. PsExec does not reliably
return when a process it started in an interactive session finishes, so completion
is detected by polling, never by the launch call returning.

usage: python run_host.py <local_script.py> <result_filename> [timeout_s]
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path

CONFIG_PATH = Path(os.environ.get("CADLOOP_HOST_CONFIG",
                                  os.path.expanduser("~/.config/sw_pc_credentials.json")))
HERE = Path(__file__).resolve().parent
REMOTE_DIR = r"C:\RRMast"
REMOTE_DIR_POSIX = REMOTE_DIR.replace("\\", "/")
SUPPORT_FILES = ("geometry.json", "oracle.json", "oracle_redrive.json")
POLL_S = 3
LAUNCH_TIMEOUT_S = 20


def config():
    return json.loads(CONFIG_PATH.read_text())


def ssh_base(c):
    return ["ssh", "-i", c["ssh_key"], "%s@%s" % (c["ssh_user"], c["ssh_host"])]


def remote(c, command, timeout=60):
    return subprocess.run(ssh_base(c) + [command], capture_output=True, text=True, timeout=timeout)


def upload(c, local: Path, name: str):
    target = "%s@%s:%s/%s" % (c["ssh_user"], c["ssh_host"], REMOTE_DIR_POSIX, name)
    return subprocess.run(["scp", "-i", c["ssh_key"], str(local), target],
                          capture_output=True, text=True)


def download(c, name: str, local: Path):
    source = "%s@%s:%s/%s" % (c["ssh_user"], c["ssh_host"], REMOTE_DIR_POSIX, name)
    return subprocess.run(["scp", "-i", c["ssh_key"], source, str(local)],
                          capture_output=True, text=True)


def clear_solidworks(c):
    remote(c, "taskkill /F /IM SLDWORKS.exe", timeout=30)
    remote(c, "taskkill /F /IM sldworks_fs.exe", timeout=30)


def run(script: Path, result_name: str, timeout_s: int = 900):
    c = config()
    remote(c, "mkdir %s" % REMOTE_DIR)
    clear_solidworks(c)

    for name in SUPPORT_FILES:
        src = HERE / name
        if src.is_file():
            t = upload(c, src, name)
            if t.returncode != 0:
                return {"status": "error", "message": "upload %s failed: %s" % (name, t.stderr.strip())}
    t = upload(c, script, script.name)
    if t.returncode != 0:
        return {"status": "error", "message": "upload %s failed: %s" % (script.name, t.stderr.strip())}

    remote_result = "%s\\%s" % (REMOTE_DIR, result_name)
    remote(c, 'del /Q "%s"' % remote_result)

    launch = ('%s -accepteula -i %d -u %s -p %s "%s" %s\\%s %s'
              % (c["psexec_path"], c["session_id"], c["windows_user"], c["windows_password"],
                 c["python_path"], REMOTE_DIR, script.name, REMOTE_DIR))
    try:
        subprocess.run(ssh_base(c) + [launch], capture_output=True, text=True,
                       timeout=LAUNCH_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        pass

    deadline = time.time() + timeout_s
    produced = False
    while time.time() < deadline:
        probe = remote(c, 'if exist "%s" echo READY' % remote_result, timeout=15)
        if "READY" in probe.stdout:
            produced = True
            break
        time.sleep(POLL_S)

    clear_solidworks(c)
    if not produced:
        return {"status": "error", "message": "%s not produced within %ds" % (result_name, timeout_s)}

    local = HERE / result_name
    download(c, result_name, local)
    if not local.is_file():
        return {"status": "error", "message": "%s could not be retrieved" % result_name}
    return json.loads(local.read_text())


def main():
    script = Path(sys.argv[1]).resolve()
    result_name = sys.argv[2]
    timeout_s = int(sys.argv[3]) if len(sys.argv) > 3 else 900
    out = run(script, result_name, timeout_s)
    print(json.dumps(out, indent=2))
    return 0 if out.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
