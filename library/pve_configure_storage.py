#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: pve_configure_storage
short_description: Manages Proxmox VE storage configurations
description:
    - Creates and modifies storage configurations
    - Supports all Proxmox storage backends
    - Manages storage content types
    - Handles directory permissions
    - Configures backup retention policies
    - Preserves existing data during modifications
version_added: "1.0"
options:
    config_file:
        description:
            - Path to Proxmox storage configuration file
            - If not specified, uses default path /etc/pve/storage.cfg
        required: false
        type: str
    desired_storage:
        description:
            - List of storage configurations to be applied
        required: true
        type: list
        elements: dict
        suboptions:
            name:
                description: Storage identifier
                type: str
                required: true
            type:
                description: Storage backend type
                type: str
                choices: ['dir', 'nfs', 'cifs', 'pbs', 'rbd', 'zfspool', 'lvmthin', 'iscsi', 'glusterfs', 'cephfs']
                default: dir
            state:
                description: Desired state of the storage
                type: str
                choices: ['present', 'absent']
                default: present
            path:
                description: Storage directory path (for dir type)
                type: str
            server:
                description: Server hostname/IP (for nfs, cifs, pbs)
                type: str
            export:
                description: NFS export path
                type: str
            share:
                description: CIFS share name
                type: str
            username:
                description: Authentication username
                type: str
            password:
                description: Authentication password
                type: str
            pool:
                description: Pool name (for rbd, zfspool)
                type: str
            monhost:
                description: Ceph monitor host
                type: str
            vgname:
                description: LVM volume group name
                type: str
            thinpool:
                description: LVM thin pool name
                type: str
            portal:
                description: iSCSI portal address
                type: str
            target:
                description: iSCSI target name
                type: str
            volume:
                description: GlusterFS volume name
                type: str
            content:
                description: List of enabled content types
                type: list
                elements: str
                choices: ['iso', 'vztmpl', 'backup', 'rootdir', 'images', 'snippets']
            prune_backups:
                description: Backup retention policy
                type: str
            max_protected_backups:
                description: Maximum number of protected backups
                type: int
"""

import os
import subprocess

from ansible.module_utils.basic import AnsibleModule


class ProxmoxStorageManager:
    def __init__(self, config_file=None):
        self.results = []
        self.changed = False
        self.command_queue = []
        self.config_file = config_file or "/etc/pve/storage.cfg"

    def execute_command(self, command):
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def ensure_directory(self, path):
        if not os.path.exists(path):
            try:
                os.makedirs(path, mode=0o755)
                return True, f"Created directory {path}"
            except Exception as e:
                return False, str(e)
        return False, f"Directory {path} already exists"

    def get_current_storage(self):
        try:
            with open(self.config_file, "r") as f:
                storage_data = []
                current_storage = None

                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith(
                        (
                            "dir:",
                            "nfs:",
                            "cifs:",
                            "pbs:",
                            "rbd:",
                            "zfspool:",
                            "lvmthin:",
                            "iscsi:",
                            "glusterfs:",
                            "cephfs:",
                        )
                    ):
                        if current_storage:
                            storage_data.append(current_storage)
                        storage_type, name = line.split(" ", 1)
                        current_storage = {
                            "storage": name,
                            "type": storage_type.rstrip(":"),
                            "content": [],
                        }
                    elif current_storage and ":" in line:
                        key, value = line.split(":", 1)
                        if key.strip() == "content":
                            current_storage["content"] = [
                                x.strip() for x in value.strip().split(",")
                            ]
                        else:
                            current_storage[key.strip()] = value.strip()

                if current_storage:
                    storage_data.append(current_storage)

                return storage_data
        except FileNotFoundError:
            return []

    def build_storage_commands(self, name, desired_config, current_config=None):
        commands = []
        storage_type = desired_config.get("type", "dir")

        if not current_config:
            cmd = f"pvesm add {storage_type} {name}"

            if desired_config.get("content"):
                cmd += f" --content {','.join(desired_config['content'])}"

            if storage_type == "dir":
                cmd += f" --path {desired_config['path']}"

            elif storage_type == "nfs":
                cmd += f" --server {desired_config['server']}"
                cmd += f" --export {desired_config['export']}"
                if desired_config.get("options"):
                    cmd += f" --options {desired_config['options']}"

            elif storage_type == "cifs":
                cmd += f" --server {desired_config['server']}"
                cmd += f" --share {desired_config['share']}"
                if desired_config.get("username"):
                    cmd += f" --username {desired_config['username']}"
                if desired_config.get("password"):
                    cmd += f" --password {desired_config['password']}"

            elif storage_type == "pbs":
                cmd += f" --server {desired_config['server']}"
                cmd += f" --datastore {desired_config['datastore']}"
                if desired_config.get("username"):
                    cmd += f" --username {desired_config['username']}"
                if desired_config.get("password"):
                    cmd += f" --password {desired_config['password']}"

            elif storage_type == "rbd":
                cmd += f" --pool {desired_config['pool']}"
                if desired_config.get("monhost"):
                    cmd += f" --monhost {desired_config['monhost']}"
                if desired_config.get("username"):
                    cmd += f" --username {desired_config['username']}"

            elif storage_type == "zfspool":
                cmd += f" --pool {desired_config['pool']}"
                if desired_config.get("sparse"):
                    cmd += " --sparse 1"

            elif storage_type == "lvmthin":
                cmd += f" --vgname {desired_config['vgname']}"
                cmd += f" --thinpool {desired_config['thinpool']}"

            elif storage_type == "iscsi":
                cmd += f" --portal {desired_config['portal']}"
                cmd += f" --target {desired_config['target']}"

            elif storage_type == "glusterfs":
                cmd += f" --server {desired_config['server']}"
                cmd += f" --volume {desired_config['volume']}"

            elif storage_type == "cephfs":
                if desired_config.get("monhost"):
                    cmd += f" --monhost {desired_config['monhost']}"
                if desired_config.get("username"):
                    cmd += f" --username {desired_config['username']}"

            commands.append(("storage_create", cmd))

        else:
            if desired_config.get("content"):
                current_content = current_config.get("content", [])
                if set(desired_config["content"]) != set(current_content):
                    commands.append(
                        (
                            "storage_modify",
                            f"pvesm set {name} --content {','.join(desired_config['content'])}",
                        )
                    )

        if desired_config.get("prune_backups"):
            commands.append(
                (
                    "storage_prune",
                    f"pvesm set {name} --prune-backups '{desired_config['prune_backups']}'",
                )
            )

        if desired_config.get("max_protected_backups"):
            commands.append(
                (
                    "storage_protect",
                    f"pvesm set {name} --max-protected-backups {desired_config['max_protected_backups']}",
                )
            )

        return commands

    def manage_storage(self, desired_storage):
        current_storage = self.get_current_storage()
        current_storage_dict = {
            storage["storage"]: storage for storage in current_storage
        }

        for desired in desired_storage:
            name = desired.get("name")
            if not name:
                continue

            state = desired.get("state", "present")

            if state == "absent":
                if name in current_storage_dict:
                    cmd = f"pvesm remove {name}"
                    self.command_queue.append(("storage_remove", cmd))
                continue

            if desired.get("type") == "dir" and desired.get("path"):
                success, msg = self.ensure_directory(desired["path"])
                if success:
                    self.changed = True
                    self.results.append(
                        {
                            "command_type": "directory",
                            "storage": name,
                            "status": "success",
                            "details": msg,
                        }
                    )

            current = current_storage_dict.get(name)
            commands = self.build_storage_commands(name, desired, current)
            self.command_queue.extend(commands)

        for cmd_type, command in self.command_queue:
            success, output = self.execute_command(command)
            if success:
                self.changed = True
                self.results.append(
                    {"command_type": cmd_type, "command": command, "status": "success"}
                )
            else:
                self.results.append(
                    {
                        "command_type": cmd_type,
                        "command": command,
                        "status": "failed",
                        "error": output,
                    }
                )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            config_file=dict(type="str", required=False),
            desired_storage=dict(required=True, type="list", elements="dict"),
        ),
        supports_check_mode=True,
    )

    try:
        manager = ProxmoxStorageManager(module.params.get("config_file"))
        manager.manage_storage(module.params["desired_storage"])

        module.exit_json(changed=manager.changed, results=manager.results)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
