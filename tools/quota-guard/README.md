# quota-guard

A Claude Code mod that stops new subagent (`Agent`) calls while the 5-hour usage window is at or above a threshold (default 85%). It exists so a long, many-subagent job (such as translating a book) pauses itself before it uses up the window.

- Checks the live figure (`$.session.usage()`) every time an `Agent` call is about to start. Over the threshold, the call is refused with a message that says the percent, the limit and the reset time, and tells the model to stop and report.
- Shows one toast when the window first crosses the threshold, and re-arms when it drops below.
- Releases by itself after the window resets. Nothing to turn off.
- Fails open: if the usage figure is missing (an API key, not a subscription) or the hook errors, calls go through.
- Limits: subagents already running finish, so use can pass the threshold by a batch; only `Agent` is blocked; the main session is not.

## Install (Windows PowerShell)

```powershell
.\tools\quota-guard\install.ps1
```

## Install (macOS, Linux, Git Bash)

```bash
./tools/quota-guard/install.sh
```

Then run `/reload-plugins` in an open Claude Code session, or restart it. The mod is read from this folder, so keep the folder where it is while the mod is installed. Remove it with `install.ps1 -Uninstall` or `install.sh --uninstall`.

Set the threshold (1 to 100) with `claude plugin configure quota-guard`.

## Develop

```bash
claude plugin validate tools/quota-guard
claude plugin test tools/quota-guard
```

The validator notes a "gating hook without .catch" on purpose: no handler means fail open.
