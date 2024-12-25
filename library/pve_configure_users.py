#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
---
module: pve_configure_users
short_description: Manages Proxmox VE user configurations
description:
    - Creates and modifies user accounts
    - Manages user permissions with precise ACL control
    - Controls user enable/disable state
    - Handles password management
    - Manages group memberships
    - Manages API tokens and permissions
    - Controls SSH access
version_added: "1.0"
options:
    desired_users:
        description:
            - List of user configurations to apply
        required: true
        type: list
        elements: dict
        suboptions:
            name:
                description: Username (without @pam)
                type: str
                required: true
            password:
                description: User password
                type: str
                required: false
            email:
                description: User email address
                type: str
                required: false
            enabled:
                description: Enable or disable user
                type: bool
                default: true
            comment:
                description: User description
                type: str
                required: false
            groups:
                description: List of groups user belongs to
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
            tokens:
                description: List of API tokens for the user
                type: list
                elements: dict
                required: false
                suboptions:
                    name:
                        description: Token name
                        type: str
                        required: true
                    privsep:
                        description: Privilege separation
                        type: bool
                        default: true
                    permissions:
                        description: List of path-based permissions for token
                        type: list
                        elements: dict
                        required: false
            ssh_allowed:
                description: Allow SSH access for user
                type: bool
                default: false
            state:
                description: Desired state
                choices: [ present, absent ]
                default: present
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pve_base_utils import get_proxmox_data
import subprocess
import json
from datetime import datetime

class ProxmoxUserManager:
    def __init__(self):
        self.results = []
        self.changed = False
        self.current_state = None
        self.change_tracker = {}

    def execute_command(self, command):
        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr

    def get_current_state(self):
        if self.current_state is None:
            proxmox_data = get_proxmox_data()
            self.current_state = proxmox_data['users']
            
            for user in self.current_state:
                userid = user['userid']
                user['acls'] = [
                    acl for acl in proxmox_data['acls'] 
                    if acl['type'] == 'user' and acl['ugid'] == userid
                ]
                user['groups'] = [
                    group['groupid'] for group in proxmox_data['groups']
                    if userid in group.get('users', '').split(',')
                ]
                
                # Get user tokens
                success, tokens_output = self.execute_command(f"pvesh get /access/users/{userid}/token --output-format=json")
                user['tokens'] = json.loads(tokens_output) if success else []
        
        return self.current_state

    def track_change(self, username, category, change, details=''):
        if username not in self.change_tracker:
            self.change_tracker[username] = {
                'account': [],
                'properties': [],
                'password': [],
                'acls': [],
                'groups': [],
                'tokens': [],
                'ssh': []
            }
        
        self.change_tracker[username][category].append({
            'action': change,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def manage_user_tokens(self, username, desired_tokens):
        if not desired_tokens:
            return

        success, output = self.execute_command(f"pvesh get /access/users/{username}@pam/token --output-format=json")
        current_tokens = json.loads(output) if success else []

        for token in desired_tokens:
            token_id = f"{username}@pam!{token['name']}"
            token_exists = any(t['tokenid'] == token['name'] for t in current_tokens)
            
            if not token_exists:
                cmd = f"pveum user token add {username}@pam {token['name']}"
                if 'privsep' in token:
                    cmd += f" --privsep {1 if token['privsep'] else 0}"
                
                success, _ = self.execute_command(cmd)
                if success:
                    self.track_change(username, 'tokens', 'create', f"Token {token['name']} created")

            if token.get('permissions'):
                success, acls_output = self.execute_command("pveum acl list --output-format=json")
                if success:
                    current_acls = json.loads(acls_output)
                    for acl in current_acls:
                        if acl.get('ugid') == token_id:
                            cmd = f"pveum acl delete {acl['path']} -token {token_id} -role {acl['roleid']}"
                            self.execute_command(cmd)

                for perm in token['permissions']:
                    for role in perm['roles']:
                        cmd = f"pveum acl modify {perm['path']} -token {token_id} -role {role}"
                        success, _ = self.execute_command(cmd)
                        if success:
                            self.track_change(username, 'tokens', 'permission', 
                                            f"Added {role} permission to token {token['name']} for path {perm['path']}")

    def manage_user_acls(self, username, desired_acls):
        current_user = next(
            (u for u in self.get_current_state() 
             if u['userid'] == f"{username}@pam"),
            {'acls': []}
        )

        for acl in current_user['acls']:
            cmd = f"pveum acl delete {acl['path']} -user {username}@pam -role {acl['roleid']}"
            success, _ = self.execute_command(cmd)
            if success:
                self.track_change(username, 'acls', 'remove', f"Removed {acl['roleid']} from {acl['path']}")

        for acl in desired_acls:
            for role in acl['roles']:
                cmd = f"pveum acl modify {acl['path']} -user {username}@pam -role {role}"
                success, _ = self.execute_command(cmd)
                if success:
                    self.track_change(username, 'acls', 'add', f"Added {role} to {acl['path']}")

    def manage_user_groups(self, username, desired_groups):
        current_user = next(
            (u for u in self.get_current_state() 
             if u['userid'] == f"{username}@pam"),
            {'groups': []}
        )

        for group in current_user['groups']:
            if group not in desired_groups:
                cmd = f"pveum user modify {username}@pam -group {group} -delete"
                success, _ = self.execute_command(cmd)
                if success:
                    self.track_change(username, 'groups', 'remove', f"Removed from {group}")

        for group in desired_groups:
            if group not in current_user['groups']:
                cmd = f"pveum user modify {username}@pam -group {group}"
                success, _ = self.execute_command(cmd)
                if success:
                    self.track_change(username, 'groups', 'add', f"Added to {group}")

    def format_changes(self, username):
        changes = self.change_tracker.get(username, {})
        if not any(changes.values()):
            return "No changes required"

        formatted = []
        for category, category_changes in changes.items():
            if category_changes:
                formatted.extend([
                    f"✓ {change['action']}: {change['details']}"
                    for change in category_changes
                ])
        
        return "\n".join(formatted)

    def manage_users(self, desired_users):
        for desired in desired_users:
            username = desired['name']
            current_user = next(
                (u for u in self.get_current_state() 
                 if u['userid'] == f"{username}@pam"),
                None
            )
            
            if desired.get('state', 'present') == 'present':
                if not current_user:
                    cmd = f"pveum user add {username}@pam"
                    if desired.get('email'):
                        cmd += f" -email '{desired['email']}'"
                    if desired.get('comment'):
                        cmd += f" -comment '{desired['comment']}'"
                    if 'enabled' in desired:
                        cmd += f" -enable {1 if desired['enabled'] else 0}"
                    
                    success, _ = self.execute_command(cmd)
                    if success:
                        self.track_change(username, 'account', 'create', 'User created')
                        
                        if desired.get('password'):
                            pwd_cmd = f"printf '%s\n%s\n' '{desired['password']}' '{desired['password']}' | pveum passwd {username}@pam"
                            success, _ = self.execute_command(pwd_cmd)
                            if success:
                                self.track_change(username, 'password', 'set', 'Initial password set')
                
                else:
                    update_cmd = f"pveum user modify {username}@pam"
                    update_needed = False
                    
                    if desired.get('email') != current_user.get('email'):
                        update_cmd += f" -email '{desired['email']}'"
                        update_needed = True
                    if desired.get('comment') != current_user.get('comment'):
                        update_cmd += f" -comment '{desired['comment']}'"
                        update_needed = True
                    if desired.get('enabled') != current_user.get('enable'):
                        update_cmd += f" -enable {1 if desired['enabled'] else 0}"
                        update_needed = True
                    
                    if update_needed:
                        success, _ = self.execute_command(update_cmd)
                        if success:
                            self.track_change(username, 'properties', 'update', 'User properties updated')
                    
                    if desired.get('password'):
                        pwd_cmd = f"printf '%s\n%s\n' '{desired['password']}' '{desired['password']}' | pveum passwd {username}@pam"
                        success, _ = self.execute_command(pwd_cmd)
                        if success:
                            self.track_change(username, 'password', 'update', 'Password updated')

                # Handle SSH access
                if 'ssh_allowed' in desired:
                    ssh_cmd = f"pveum user modify {username}@pam -enable-ssh {1 if desired['ssh_allowed'] else 0}"
                    success, _ = self.execute_command(ssh_cmd)
                    if success:
                        self.track_change(username, 'ssh', 'update', 
                                        f"SSH access {'enabled' if desired['ssh_allowed'] else 'disabled'}")

                # Handle ACLs, groups, and tokens
                if desired.get('permissions'):
                    self.manage_user_acls(username, desired['permissions'])
                if desired.get('groups'):
                    self.manage_user_groups(username, desired['groups'])
                if desired.get('tokens'):
                    self.manage_user_tokens(username, desired['tokens'])

            else:  # state == 'absent'
                if current_user:
                    for acl in current_user['acls']:
                        cmd = f"pveum acl delete {acl['path']} -user {username}@pam -role {acl['roleid']}"
                        self.execute_command(cmd)
                    
                    cmd = f"pveum user delete {username}@pam"
                    success, _ = self.execute_command(cmd)
                    if success:
                        self.track_change(username, 'account', 'remove', 'User removed')

            changes = self.change_tracker.get(username, {})
            if any(changes.values()):
                self.changed = True
                self.results.append({
                    'name': username,
                    'status': 'changed',
                    'details': self.format_changes(username),
                    'changes': {
                        category: [change['details'] for change in category_changes]
                        for category, category_changes in changes.items()
                        if category_changes
                    }
                })
            else:
                self.results.append({
                    'name': username,
                    'status': 'ok',
                    'details': 'No changes required'
                })

def main():
    module = AnsibleModule(
        argument_spec=dict(
            desired_users=dict(required=True, type='list', elements='dict')
        ),
        supports_check_mode=True
    )
    
    try:
        manager = ProxmoxUserManager()
        manager.manage_users(module.params['desired_users'])
        
        module.exit_json(
            changed=manager.changed,
            results=manager.results
        )
    except Exception as e:
        module.fail_json(msg=str(e))

if __name__ == '__main__':
    main()
