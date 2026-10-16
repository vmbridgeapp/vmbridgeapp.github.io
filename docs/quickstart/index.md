# Quickstart

Give an agent a Parallels Desktop virtual machine. The host needs macOS 14 or later and Parallels Desktop Pro or Business.

## Install the command

```
git clone https://github.com/AlexmChadwick/Parallels-Agents.git
cd Parallels-Agents
./scripts/install.sh
```

That installs `vmbridge`. `parallels-pro-mcp` and `guest-vm-agents` are the same command. A notarized DMG ships with the GitHub release when a signed build is published. It is not a file on this website.

## Start the trial

Open VMBridge. The price is $9.99 one-time, with a 7-day free trial. The trial is full-featured and starts at first launch on that Mac. Buy opens the Polar checkout. Polar (Polar Software, Inc.) processes the payment as merchant of record.

## Connect Claude Code, Codex, or Cursor

```
vmbridge connect claude-code
vmbridge connect codex
vmbridge connect cursor
vmbridge connect list
```

Quit the agent and open it again so it loads the server. The same command covers Claude Desktop, Gemini CLI, VS Code, Windsurf, Cline, and the other MCP clients the app lists.

## Let it look at the guest

The agent can take a screenshot, read the text on the screen, click, and type. Those tools use the virtual machine's keyboard and mouse. They do not need Parallels Tools, which is how an agent can drive an installer. Commands, files, and the clipboard do need Parallels Tools.

## Stop it

Pause all agents from the menu-bar app, or turn off agent control for that VM. Either one is checked on the next tool call.
