# MCP tools for a Parallels Desktop VM

VMBridge speaks MCP. An agent on the Mac starts `vmbridge` over stdio. An agent inside a VM uses the daemon on the Parallels Shared or Host-Only network, with a token that works only for that VM.

## What an agent can do

- See the screen and read the text on it (vm_screenshot, vm_read_screen).
- Click, type, scroll, and drag with the VM's own keyboard and mouse.
- Run commands and move files (vm_run, vm_exec, vm_copy_to_guest, vm_copy_from_guest).
- List and focus windows, open an app or URL, and search files by name.
- Start, stop, pause, clone, and create VMs, and take and revert snapshots.
- Sign in at the login screen without the agent seeing the password.

## What it does not do

- It does not record video of the VM.
- It does not read the guest accessibility tree. On-screen text is OCR.
- It does not rename snapshots. prlctl has no rename.
- It is not a hypervisor. Parallels Desktop runs the VM.
