#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: pve_configure_groups
short_description: Manages Proxmox VE group configurations
description:
    - Creates and modifies group configurations
    - Manages group roles and permissions
    - Handles group memberships
    - Provides detailed change tracking
version_added: "1.0"
options:
    desired_groups:
        description:
            - List of group configurations to apply
        required: true
        type: list
        elements: dict
        suboptions:
            name:
                description: Group name
                type: str
                required: true
            comment:
                description: Group description
                type: str
                required: false
            members:
                description: List of group members
                type: list
                elements: str
                required: false
            permissions:
                description: List of path-based permissions
                type: list
                elements: dict
                required: false
                suboptions:
                    path:
                        description: Permission path
                        type: str
                        required: true
                    roles:
                        description: Roles for this path
                        type: list
                        elements: str
                        required: true
"""

import json
import subprocess
from datetime import datetime

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pve_base_utils import get_proxmox_data


class ProxmoxGroupManager:
    def __init__(self):
        self.results = []
        self.changed = False
        self.current_state = None
        self.command_queue = []

    def execute_command(self, command):
        try:
            result = subprocess.run(
                command, shell=True, check=True, capture_output=True, text=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def get_current_state(self):
        if self.current_state is None:
            proxmox_data = get_proxmox_data()
            self.current_state = {}

            for group in proxmox_data.get("groups", []):
                groupid = group.get("groupid")
                if groupid:
                    self.current_state[groupid] = {
                        "comment": group.get("comment", ""),
                        "members": (
                            group.get("users", "").split(",")
                            if group.get("users")
                            else []
                        ),
                        "permissions": [
                            {"path": acl.get("path"), "roles": [acl.get("roleid")]}
                            for acl in proxmox_data.get("acls", [])
                            if acl.get("type") == "group" and acl.get("ugid") == groupid
                        ],
                    }
        return self.current_state

    def build_group_commands(self, groupname, desired_config):
        commands = []
        current_config = self.current_state.get(groupname, {})

        if not current_config:
            cmd = f"pveum group add {groupname}"
            if desired_config.get("comment"):
                cmd += f" -comment '{desired_config.get('comment')}'"
            commands.append(("group_create", cmd))
        else:
            if desired_config.get("comment") != current_config.get("comment"):
                commands.append(
                    (
                        "group_modify",
                        f"pveum group modify {groupname} -comment '{desired_config.get('comment')}'",
                    )
                )

        return commands

    def build_permission_commands(self, groupname, desired_perms, current_perms):
        commands = []

        for perm in current_perms:
            for role in perm.get("roles", []):
                commands.append(
                    (
                        "acl_remove",
                        f"pveum acl delete {perm.get('path')} -group {groupname} -role {role}",
                    )
                )

        for perm in desired_perms:
            for role in perm.get("roles", []):
                commands.append(
                    (
                        "acl_add",
                        f"pveum acl modify {perm.get('path')} -group {groupname} -role {role}",
                    )
                )

        return commands

    def build_member_commands(self, groupname, desired_members, current_members):
        commands = []

        for member in current_members:
            if member and member not in desired_members:
                commands.append(
                    (
                        "member_remove",
                        f"pveum user modify {member}@pam -group {groupname} -delete",
                    )
                )

        for member in desired_members:
            if member not in current_members:
                commands.append(
                    ("member_add", f"pveum user modify {member}@pam -group {groupname}")
                )

        return commands

    def manage_groups(self, desired_groups):
        current_state = self.get_current_state()

        for desired in desired_groups:
            groupname = desired.get("name")
            if not groupname:
                continue

            current = current_state.get(groupname, {})
            self.command_queue.extend(self.build_group_commands(groupname, desired))

            if desired.get("permissions"):
                self.command_queue.extend(
                    self.build_permission_commands(
                        groupname,
                        desired.get("permissions", []),
                        current.get("permissions", []),
                    )
                )

            if desired.get("members"):
                self.command_queue.extend(
                    self.build_member_commands(
                        groupname,
                        desired.get("members", []),
                        current.get("members", []),
                    )
                )

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
            desired_groups=dict(required=True, type="list", elements="dict")
        ),
        supports_check_mode=True,
    )

    try:
        manager = ProxmoxGroupManager()
        manager.manage_groups(module.params["desired_groups"])

        module.exit_json(changed=manager.changed, results=manager.results)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
