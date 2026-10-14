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

Open VMBridge. The 7-day full-featured trial starts at first launch on that Mac. The price after the trial is $9.99 once. Buy opens the Lemon Squeezy checkout. The store is in test mode pending approval; the URL stays the same when the store is live.

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
