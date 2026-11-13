# MCP tools for a Parallels Desktop VM

VMBridge speaks MCP. An agent on the Mac starts `vmbridge` over stdio. An agent inside a VM uses the daemon on the Parallels Shared or Host-Only network, with a token that works only for that VM.

The complete reference, including every tool, parameter, and default, is on the [MCP tools page](/docs/mcp-tools/).

## Tool index

### Discovery

- `vm_list`
- `vm_status`
- `agent_status`
- `vm_log`
- `vm_doctor`
- `vm_changelog`

### Screen and input

- `vm_screenshot`
- `vm_read_screen`
- `vm_find_text`
- `vm_wait`
- `vm_click`
- `vm_click_text`
- `vm_mouse`
- `vm_cursor`
- `vm_drag`
- `vm_scroll`
- `vm_type`
- `vm_key`
- `vm_send_keys`
- `vm_act`
- `vm_set_resolution`

### Sign-in and secrets

- `vm_sign_in`
- `vm_set_signin_password`
- `vm_type_secret`

### Commands and jobs

- `vm_run`
- `vm_exec`
- `vm_job_status`
- `vm_job_stop`
- `vm_job_list`
- `vm_job_prune`

### Files and clipboard

- `vm_read_file`
- `vm_write_file`
- `vm_list_dir`
- `vm_copy_to_guest`
- `vm_copy_from_guest`
- `vm_send_to_mac`
- `vm_clipboard`
- `vm_windows`
- `vm_open`
- `vm_find_files`

### Power

- `vm_start`
- `vm_stop`
- `vm_suspend`
- `vm_resume`
- `vm_pause`
- `vm_restart`
- `vm_wait_ready`

### Snapshots and notes

- `snapshot_list`
- `snapshot_create`
- `snapshot_revert`
- `snapshot_delete`
- `agent_notes`

### Manage VMs

- `vm_create`
- `vm_finish_install`
- `vm_systems`
- `vm_clone`
- `vm_delete`
- `vm_configure`
- `vm_set_headless`
- `vm_set_network_condition`
- `vm_share_folder`
- `vm_unshare_folder`
- `vm_port_forward`
- `vm_install_tools`
- `vm_optimize_windows`
- `vm_run_ephemeral`

## What it does not do

- It does not record video of the VM.
- It does not read the guest accessibility tree. On-screen text is OCR.
- It does not rename snapshots. prlctl has no rename.
- It is not a hypervisor. Parallels Desktop runs the VM.
