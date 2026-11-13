# Install VMBridge

VMBridge is a macOS app for Parallels Desktop. The host needs macOS 14 or later and Parallels Desktop Pro or Business, because the tools use prlctl and the Parallels Virtualization SDK.

## Install the app and command

Download the DMG from the VMBridge site, drag VMBridge to Applications, and open it. The app includes the `vmbridge` command at `/Applications/VMBridge.app/Contents/Resources/cli/vmbridge`. `parallels-pro-mcp` and `guest-vm-agents` are aliases for the same command.

## Connect an agent

```
vmbridge connect claude-code
vmbridge connect list
```

The same connect command covers Claude Desktop, Codex, Cursor, VS Code, Windsurf, Cline, Gemini CLI, and other MCP clients.

## Where state lives

The default folder is ~/Library/Application Support/VMBridge. Set VMBRIDGE_HOME to move it. PARALLELS_MCP_HOME still works. On first launch an older Application Support folder is moved here, including the license file, so the trial clock is not reset. If that move fails, the older folder is still used.
