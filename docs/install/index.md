# Install VMBridge

VMBridge is a macOS app for Parallels Desktop. The host needs macOS 14 or later and Parallels Desktop Pro or Business, because the tools use prlctl and the Parallels Virtualization SDK.

## Developer install

```
git clone https://github.com/AlexmChadwick/Parallels-Agents.git
cd Parallels-Agents
./scripts/install.sh
```

That installs the `vmbridge` command. `parallels-pro-mcp` and `guest-vm-agents` are the same command.

## Connect an agent

```
vmbridge connect claude-code
vmbridge connect list
```

The same connect command covers Claude Desktop, Codex, Cursor, VS Code, Windsurf, Cline, Gemini CLI, and other MCP clients.

## Where state lives

The default folder is ~/Library/Application Support/VMBridge. Set VMBRIDGE_HOME to move it. PARALLELS_MCP_HOME still works. If the new folder does not exist and an older "Parallels Pro MCP" folder does, that older folder is kept so the trial clock is not reset.
