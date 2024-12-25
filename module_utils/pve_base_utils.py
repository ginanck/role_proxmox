#!/usr/bin/python
import json
import subprocess
from datetime import datetime

def get_proxmox_data():
    """Get all Proxmox configuration data in JSON format"""
    try:
        # Get roles
        roles_cmd = "pveum role list --output-format=json"
        roles_output = subprocess.check_output(roles_cmd, shell=True, text=True)
        roles = json.loads(roles_output)

        # Get ACLs
        acls_cmd = "pveum acl list --output-format=json"
        acls_output = subprocess.check_output(acls_cmd, shell=True, text=True)
        acls = json.loads(acls_output)

        # Get groups
        groups_cmd = "pveum group list --output-format=json"
        groups_output = subprocess.check_output(groups_cmd, shell=True, text=True)
        groups = json.loads(groups_output)

        # Get users
        users_cmd = "pveum user list --output-format=json"
        users_output = subprocess.check_output(users_cmd, shell=True, text=True)
        users = json.loads(users_output)

        return {
            'roles': roles,
            'acls': acls,
            'groups': groups,
            'users': users
        }
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to get Proxmox data: {str(e)}")
