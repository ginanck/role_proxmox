# Ansible Module Development Testing Guide

This guide provides comprehensive testing strategies for developing and debugging Ansible modules for Proxmox VE integration. This role includes both traditional CLI-based modules and modern proxmoxer-based modules.

## Table of Contents

1. [Python CLI Testing (Direct Module Testing)](#1-python-cli-testing-direct-module-testing)
2. [Ansible Module Testing (Local Development)](#2-ansible-module-testing-local-development)
3. [Interactive Development & Debugging](#3-interactive-development--debugging)
4. [Common Debugging Patterns](#4-common-debugging-patterns)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Python CLI Testing (Direct Module Testing)

### Overview
Test your module logic directly in Python without Ansible overhead. Perfect for rapid development and debugging individual functions.

### Setup

#### Step 1: Create Test Environment
```bash
cd /Users/gkorkmaz/Projects/dev/ansible_development/roles/role_proxmox

# Create testing structure
mkdir -p tests/python_cli
cd tests/python_cli
```

#### Step 2: Create Connection Test Script for CLI-based Modules
```bash
cat > test_cli_modules.py << 'EOF'
#!/usr/bin/env python3
"""
Direct Python testing for existing Proxmox CLI-based modules
"""

import sys
import os
import json
import subprocess
from pprint import pprint

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'module_utils'))

def test_cli_connection():
    """Test basic CLI connection and Proxmox utilities"""
    try:
        from pve_base_utils import get_proxmox_data

        print("🔗 Testing Proxmox CLI Connection...")
        print("-" * 50)

        # Test if pveum is available
        try:
            result = subprocess.run(['pveum', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ pveum CLI tool is available")
            else:
                print("❌ pveum CLI tool not found or not working")
                return False
        except FileNotFoundError:
            print("❌ pveum not found in PATH")
            return False

        # Test getting Proxmox data
        try:
            data = get_proxmox_data()
            print("✅ Successfully retrieved Proxmox data")
            print(f"  Users: {len(data['users'])}")
            print(f"  Groups: {len(data['groups'])}")
            print(f"  Roles: {len(data['roles'])}")
            print(f"  ACLs: {len(data['acls'])}")
            return True
        except Exception as e:
            print(f"❌ Failed to get Proxmox data: {e}")
            return False

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

def test_proxmoxer_connection():
    """Test proxmoxer API connection if available"""
    try:
        from pve_api_compatibility import CompatibleProxmoxConnection

        # Configuration - Update these with your Proxmox details
        config = {
            'host': 'your-proxmox-host.com',
            'user': 'root@pam',
            'password': 'your-password',  # or use token auth
            'verify_ssl': False
        }

        print("🔗 Testing Proxmox API Connection (proxmoxer)...")
        print(f"Host: {config['host']}")
        print(f"User: {config['user']}")
        print("-" * 50)

        # Create connection
        conn = CompatibleProxmoxConnection(**config)

        # Test connection
        if conn.test_connection():
            print("✅ Proxmoxer connection successful!")
        else:
            print("❌ Proxmoxer connection failed!")
            return None

        # Get version information
        print("\n📊 Version Information:")
        version_info = conn.get_version_info()
        for key, value in version_info.items():
            print(f"  {key}: {value}")

        # Test feature support
        print("\n🔧 Feature Support:")
        features_to_test = [
            'api_tokens', 'storage_encryption', 'vm_templates',
            'user_groups', 'sdn_support', 'backup_jobs'
        ]

        for feature in features_to_test:
            supported = conn.api_compat.is_feature_supported(feature)
            status = "✅" if supported else "❌"
            print(f"  {status} {feature}")

        return conn

    except ImportError as e:
        print(f"❌ Proxmoxer Import Error: {e}")
        print("Make sure you have installed: pip install proxmoxer requests packaging")
        return None
    except Exception as e:
        print(f"❌ Proxmoxer Connection Error: {e}")
        return None

def test_existing_modules():
    """Test existing CLI-based modules"""
    print("\n📦 Testing Existing Modules...")
    print("-" * 50)

    # Test importing existing modules
    modules_to_test = [
        'pve_configure_users',
        'pve_configure_groups',
        'pve_configure_storage',
        'pve_get_tokens'
    ]

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'library'))

    for module_name in modules_to_test:
        try:
            module = __import__(module_name)
            print(f"✅ {module_name}: Import successful")

            # Check if module has main function
            if hasattr(module, 'main'):
                print(f"  ✅ Has main() function")
            else:
                print(f"  ❌ Missing main() function")

        except ImportError as e:
            print(f"❌ {module_name}: Import failed - {e}")
        except Exception as e:
            print(f"❌ {module_name}: Error - {e}")

def test_storage_utils():
    """Test storage utilities"""
    print("\n💾 Testing Storage Utilities...")
    print("-" * 50)

    try:
        from pve_storage_utils import parse_storage_config, read_storage_config

        # Test parsing sample storage config
        sample_config = """
dir: local
	path /var/lib/vz
	content backup,vztmpl,iso,rootdir,images

dir: backups
	path /backup
	content backup
	prune-backups keep-daily=7,keep-weekly=4,keep-monthly=3
"""

        storages = parse_storage_config(sample_config)
        print(f"✅ Parsed {len(storages)} storage configurations")

        for storage in storages:
            print(f"  - {storage['name']} ({storage['type']}): {storage['path']}")

    except ImportError as e:
        print(f"❌ Storage utils import error: {e}")
    except Exception as e:
        print(f"❌ Storage utils test error: {e}")

def main():
    """Main testing function"""
    print("🚀 Proxmox Module Direct Testing")
    print("=" * 50)

    # Test CLI connection first (existing modules)
    cli_success = test_cli_connection()

    # Test existing modules
    test_existing_modules()

    # Test storage utilities
    test_storage_utils()

    # Test proxmoxer connection if available
    if cli_success:
        print("\n" + "=" * 50)
        conn = test_proxmoxer_connection()

    print("\n✨ Testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
EOF
```

#### Step 3: Create Module-Specific Tests
```bash
cat > test_user_module.py << 'EOF'
#!/usr/bin/env python3
"""
Test specific user management module functions directly
"""

import sys
import os
import json

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'module_utils'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'library'))

def test_user_module_import():
    """Test importing the user management module"""
    try:
        import pve_configure_users
        print("✅ pve_configure_users imported successfully")

        # Check for required classes/functions
        if hasattr(pve_configure_users, 'main'):
            print("  ✅ Has main() function")

        if hasattr(pve_configure_users, 'UserManager'):
            print("  ✅ Has UserManager class")
        elif hasattr(pve_configure_users, 'ProxmoxUserManager'):
            print("  ✅ Has ProxmoxUserManager class")
        else:
            print("  ❌ Missing user manager class")

        return True
    except ImportError as e:
        print(f"❌ Failed to import pve_configure_users: {e}")
        return False

def test_storage_module_import():
    """Test importing the storage management module"""
    try:
        import pve_configure_storage
        print("✅ pve_configure_storage imported successfully")

        # Check for required functions
        if hasattr(pve_configure_storage, 'main'):
            print("  ✅ Has main() function")

        if hasattr(pve_configure_storage, 'StorageManager'):
            print("  ✅ Has StorageManager class")
        else:
            print("  ❌ Missing storage manager class")

        return True
    except ImportError as e:
        print(f"❌ Failed to import pve_configure_storage: {e}")
        return False

def test_group_module_import():
    """Test importing the group management module"""
    try:
        import pve_configure_groups
        print("✅ pve_configure_groups imported successfully")

        if hasattr(pve_configure_groups, 'main'):
            print("  ✅ Has main() function")

        return True
    except ImportError as e:
        print(f"❌ Failed to import pve_configure_groups: {e}")
        return False

def test_token_module_import():
    """Test importing the token retrieval module"""
    try:
        import pve_get_tokens
        print("✅ pve_get_tokens imported successfully")

        if hasattr(pve_get_tokens, 'main'):
            print("  ✅ Has main() function")

        if hasattr(pve_get_tokens, 'TokenReader'):
            print("  ✅ Has TokenReader class")
        else:
            print("  ❌ Missing TokenReader class")

        return True
    except ImportError as e:
        print(f"❌ Failed to import pve_get_tokens: {e}")
        return False

def test_module_parameters():
    """Test module parameter validation"""
    print("\n🧪 Testing Module Parameters...")
    print("-" * 50)

    # Test user module parameters
    user_test_params = {
        'desired_users': [
            {
                'name': 'testuser',
                'password': 'testpass',
                'email': 'test@example.com',
                'enabled': True,
                'comment': 'Test user',
                'groups': ['testgroup'],
                'permissions': [
                    {
                        'path': '/',
                        'roles': ['PVEAuditor']
                    }
                ]
            }
        ]
    }

    # Test storage module parameters
    storage_test_params = {
        'desired_storage': [
            {
                'name': 'test-storage',
                'type': 'dir',
                'state': 'present',
                'path': '/var/lib/vz/test',
                'content': ['backup', 'iso']
            }
        ]
    }

    print("✅ User module test parameters:")
    print(f"  Users to configure: {len(user_test_params['desired_users'])}")

    print("✅ Storage module test parameters:")
    print(f"  Storages to configure: {len(storage_test_params['desired_storage'])}")

def main():
    """Main testing function"""
    print("🧪 Module-Specific Testing")
    print("=" * 50)

    # Test all module imports
    user_ok = test_user_module_import()
    storage_ok = test_storage_module_import()
    group_ok = test_group_module_import()
    token_ok = test_token_module_import()

    # Test parameters
    test_module_parameters()

    print(f"\n📊 Import Results:")
    print(f"  Users: {'✅' if user_ok else '❌'}")
    print(f"  Storage: {'✅' if storage_ok else '❌'}")
    print(f"  Groups: {'✅' if group_ok else '❌'}")
    print(f"  Tokens: {'✅' if token_ok else '❌'}")

    print("\n✨ Module testing completed!")

if __name__ == "__main__":
    main()
EOF
```

#### Step 4: Run Tests
```bash
# Make scripts executable
chmod +x test_cli_modules.py test_user_module.py

# Run CLI modules test (works on Proxmox host or with CLI access)
python3 test_cli_modules.py

# Run module-specific tests
python3 test_user_module.py

# Note: Update connection details in test_cli_modules.py if testing proxmoxer connection
```

---

## 2. Ansible Module Testing (Local Development)

### Overview
Test your modules in an Ansible environment with proper module loading, variable handling, and output formatting.

### Setup

#### Step 1: Create Ansible Test Environment
```bash
cd /Users/gkorkmaz/Projects/dev/ansible_development/roles/role_proxmox

# Create ansible testing structure
mkdir -p tests/ansible
cd tests/ansible
```

#### Step 2: Create Ansible Configuration
```bash
cat > ansible.cfg << 'EOF'
[defaults]
inventory = inventory
host_key_checking = False
library = ../../library
module_utils = ../../module_utils
stdout_callback = yaml
timeout = 30
gathering = explicit

[inventory]
enable_plugins = host_list, script, auto, yaml, ini, toml

[ssh_connection]
pipelining = True
EOF
```

```bash
cat > inventory << 'EOF'
[local]
localhost ansible_connection=local

[proxmox_test]
localhost ansible_connection=local
EOF
```

#### Step 3: Create Test Playbooks

**Basic Module Test (CLI-based modules):**
```bash
cat > test_basic.yml << 'EOF'
---
- name: Basic Module Testing
  hosts: localhost
  gather_facts: false
  vars:
    # Test users configuration
    test_users:
      - name: "ansible-test"
        password: "testpass123"
        email: "ansible-test@example.com"
        enabled: true
        comment: "Ansible test user"
        groups: ["testgroup"]
        permissions:
          - path: "/"
            roles: ["PVEAuditor"]

    # Test storage configuration
    test_storage:
      - name: "ansible-test-storage"
        type: "dir"
        state: "present"
        path: "/var/lib/vz/ansible-test"
        content: ["backup", "iso"]

  tasks:
    - name: Test user management module
      pve_configure_users:
        desired_users: "{{ test_users }}"
      register: user_result

    - name: Display user management results
      debug:
        msg: |
          User Management Result:
          Changed: {{ user_result.changed }}
          Created Users: {{ user_result.created_users | default([]) | length }}
          Modified Users: {{ user_result.modified_users | default([]) | length }}

    - name: Test storage management module
      pve_configure_storage:
        desired_storage: "{{ test_storage }}"
      register: storage_result

    - name: Display storage management results
      debug:
        msg: |
          Storage Management Result:
          Changed: {{ storage_result.changed }}
          Created Storage: {{ storage_result.created_storage | default([]) | length }}
          Modified Storage: {{ storage_result.modified_storage | default([]) | length }}

    - name: Test token retrieval
      pve_get_tokens:
        token_file: "/etc/pve/priv/token.cfg"
      register: token_result
      ignore_errors: true

    - name: Display token results
      debug:
        msg: |
          Token Retrieval Result:
          Tokens Found: {{ token_result.tokens | default([]) | length }}
      when: token_result is defined and not token_result.failed

    - name: Clean up test user
      pve_configure_users:
        desired_users: []
      register: cleanup_result
      when: user_result.changed

    - name: Clean up test storage
      pve_configure_storage:
        desired_storage:
          - name: "ansible-test-storage"
            state: "absent"
      register: storage_cleanup
      when: storage_result.changed
EOF
```

**Comprehensive Testing Playbook:**
```bash
cat > test_comprehensive.yml << 'EOF'
---
- name: Comprehensive Module Testing
  hosts: localhost
  gather_facts: false
  vars:
    # Multiple test users
    test_users:
      - name: "test-user-1"
        password: "pass123"
        email: "user1@test.com"
        comment: "Test user 1"
        enabled: true
        groups: ["testgroup1"]
        permissions:
          - path: "/"
            roles: ["PVEAuditor"]
      - name: "test-user-2"
        password: "pass456"
        email: "user2@test.com"
        comment: "Test user 2"
        enabled: true
        groups: ["testgroup1", "testgroup2"]
        permissions:
          - path: "/vms"
            roles: ["PVEVMUser"]

    # Multiple test groups
    test_groups:
      - name: "testgroup1"
        comment: "Test group 1"
        members: ["test-user-1", "test-user-2"]
        permissions:
          - path: "/"
            roles: ["PVEAuditor"]
      - name: "testgroup2"
        comment: "Test group 2"
        members: ["test-user-2"]
        permissions:
          - path: "/vms"
            roles: ["PVEVMUser"]

    # Multiple test storages
    test_storages:
      - name: "test-storage-1"
        type: "dir"
        state: "present"
        path: "/var/lib/vz/test1"
        content: ["backup"]
      - name: "test-storage-2"
        type: "dir"
        state: "present"
        path: "/var/lib/vz/test2"
        content: ["iso", "backup"]

  tasks:
    - name: Create test groups first
      pve_configure_groups:
        desired_groups: "{{ test_groups }}"
      register: group_results

    - name: Display group creation results
      debug:
        msg: |
          Group Management Result:
          Changed: {{ group_results.changed }}
          Created Groups: {{ group_results.created_groups | default([]) | length }}

    - name: Create multiple test users
      pve_configure_users:
        desired_users: "{{ test_users }}"
      register: user_results

    - name: Display user creation results
      debug:
        msg: |
          User Management Result:
          Changed: {{ user_results.changed }}
          Created Users: {{ user_results.created_users | default([]) | length }}
          Modified Users: {{ user_results.modified_users | default([]) | length }}

    - name: Create multiple test storages
      pve_configure_storage:
        desired_storage: "{{ test_storages }}"
      register: storage_results

    - name: Display storage creation results
      debug:
        msg: |
          Storage Management Result:
          Changed: {{ storage_results.changed }}
          Created Storage: {{ storage_results.created_storage | default([]) | length }}

    - name: Test idempotency - run user config again
      pve_configure_users:
        desired_users: "{{ test_users }}"
      register: idempotency_test

    - name: Display idempotency results
      debug:
        msg: |
          Idempotency Test:
          Changed: {{ idempotency_test.changed }}
          (Should be false if idempotent)

    - name: Clean up test resources
      block:
        - name: Remove test users
          pve_configure_users:
            desired_users: []
          register: user_cleanup

        - name: Remove test groups
          pve_configure_groups:
            desired_groups: []
          register: group_cleanup

        - name: Remove test storages
          pve_configure_storage:
            desired_storage:
              - name: "test-storage-1"
                state: "absent"
              - name: "test-storage-2"
                state: "absent"
          register: storage_cleanup

    - name: Display cleanup results
      debug:
        msg: |
          Cleanup completed:
          Users: {{ user_cleanup.changed | default(false) }}
          Groups: {{ group_cleanup.changed | default(false) }}
          Storage: {{ storage_cleanup.changed | default(false) }}
EOF
```

**Debug Playbook:**
```bash
cat > test_debug.yml << 'EOF'
---
- name: Debug Module Development
  hosts: localhost
  gather_facts: false
  vars:
    # Simple debug configuration
    debug_user:
      - name: "debug-user"
        password: "debugpass"
        email: "debug@test.com"
        enabled: true
        comment: "Debug test user"
        groups: ["debuggroup"]

    debug_storage:
      - name: "debug-storage"
        type: "dir"
        state: "present"
        path: "/var/lib/vz/debug"
        content: ["backup"]

  tasks:
    - name: Debug user module with maximum verbosity
      pve_configure_users:
        desired_users: "{{ debug_user }}"
      register: debug_user_result

    - name: Show complete user module output
      debug:
        var: debug_user_result
        verbosity: 0

    - name: Debug storage module with maximum verbosity
      pve_configure_storage:
        desired_storage: "{{ debug_storage }}"
      register: debug_storage_result

    - name: Show complete storage module output
      debug:
        var: debug_storage_result
        verbosity: 0

    - name: Debug token retrieval
      pve_get_tokens:
        token_file: "/etc/pve/priv/token.cfg"
      register: debug_token_result
      ignore_errors: true

    - name: Show token retrieval output
      debug:
        var: debug_token_result
        verbosity: 0
      when: debug_token_result is defined

    - name: Clean up debug resources
      block:
        - name: Remove debug user
          pve_configure_users:
            desired_users: []
          register: user_cleanup
          when: debug_user_result.changed

        - name: Remove debug storage
          pve_configure_storage:
            desired_storage:
              - name: "debug-storage"
                state: "absent"
          register: storage_cleanup
          when: debug_storage_result.changed

    - name: Show cleanup results
      debug:
        msg: |
          Cleanup Results:
          User cleanup: {{ user_cleanup.changed | default(false) }}
          Storage cleanup: {{ storage_cleanup.changed | default(false) }}
EOF
```

#### Step 4: Run Ansible Tests
```bash
# Basic test
ansible-playbook test_basic.yml -v

# Comprehensive test
ansible-playbook test_comprehensive.yml -v

# Debug with maximum verbosity
ansible-playbook test_debug.yml -vvv

# Test specific tags
ansible-playbook test_comprehensive.yml --tags "create" -v

# Check syntax only
ansible-playbook test_basic.yml --syntax-check

# Dry run (check mode)
ansible-playbook test_basic.yml --check -v
```

---

## 3. Interactive Development & Debugging

### Overview
Interactive testing using Python REPL for step-by-step debugging and exploration of API responses.

### Setup

#### Step 1: Create Interactive Testing Script
```bash
cd /Users/gkorkmaz/Projects/dev/ansible_development/roles/role_proxmox/tests
cat > interactive_debug.py << 'EOF'
#!/usr/bin/env python3
"""
Interactive debugging session setup
"""

import sys
import os
import json
from pprint import pprint

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'module_utils'))

def setup_cli_environment():
    """Setup CLI environment for interactive testing"""
    from pve_base_utils import get_proxmox_data

    print("Setting up Proxmox CLI environment...")
    try:
        data = get_proxmox_data()
        print("✅ CLI environment ready!")
        print(f"  Users: {len(data['users'])}")
        print(f"  Groups: {len(data['groups'])}")
        print(f"  Roles: {len(data['roles'])}")
        print(f"  ACLs: {len(data['acls'])}")
        return data
    except Exception as e:
        print(f"❌ CLI setup failed: {e}")
        return None

def setup_proxmoxer_connection():
    """Setup and return a Proxmox connection for interactive use"""
    try:
        from pve_api_compatibility import CompatibleProxmoxConnection

        # Configuration
        config = {
            'host': 'your-proxmox-host.com',
            'user': 'root@pam',
            'password': 'your-password',
            'verify_ssl': False
        }

        print("Setting up Proxmoxer connection...")
        conn = CompatibleProxmoxConnection(**config)

        if conn.test_connection():
            print("✅ Proxmoxer connected successfully!")
            return conn
        else:
            print("❌ Proxmoxer connection failed!")
            return None
    except ImportError:
        print("❌ Proxmoxer not available")
        return None

def explore_cli_tools():
    """Helper function to explore CLI tools"""
    print("\n🔍 Available CLI tools:")
    print("pveum user list --output-format=json    # Get users")
    print("pveum group list --output-format=json   # Get groups")
    print("pveum role list --output-format=json    # Get roles")
    print("pveum acl list --output-format=json     # Get ACLs")
    print("cat /etc/pve/storage.cfg                # Storage config")
    print("cat /etc/pve/priv/token.cfg             # API tokens")
    print("\n💡 Use get_proxmox_data() to get all data")

def explore_proxmoxer_api(conn):
    """Helper function to explore proxmoxer API endpoints"""
    if not conn:
        print("❌ No proxmoxer connection available")
        return

    print("\n🔍 Available Proxmoxer API endpoints:")
    print("conn.proxmox.access.users.get()  # Get users")
    print("conn.proxmox.storage.get()       # Get storage")
    print("conn.proxmox.nodes.get()         # Get nodes")
    print("conn.proxmox.version.get()       # Get version")
    print("\n💡 Use pprint() to pretty-print results")
    print("💡 Use help(conn.proxmox) for more info")

def debug_user_operations(conn, userid="interactive-test@pve"):
    """Debug user operations step by step"""
    print(f"\n🧪 Debugging user operations for: {userid}")

    try:
        # Step 1: Get all users
        print("\n1️⃣ Getting all users...")
        users = conn.proxmox.access.users.get()
        print(f"Found {len(users)} users")

        # Step 2: Check if test user exists
        print(f"\n2️⃣ Checking if {userid} exists...")
        test_user = None
        for user in users:
            if user.get('userid') == userid:
                test_user = user
                break

        if test_user:
            print(f"✅ User exists: {test_user}")
        else:
            print("❌ User doesn't exist")

        # Step 3: Try to create user
        print(f"\n3️⃣ Attempting to create {userid}...")
        try:
            if not test_user:
                result = conn.create_user_compatible(
                    userid=userid,
                    password="testpass123",
                    email="interactive@test.com",
                    comment="Interactive test user"
                )
                print(f"✅ User created: {result}")
            else:
                print("⚠️ User already exists, skipping creation")
        except Exception as e:
            print(f"❌ Creation failed: {e}")

        # Step 4: Get updated user list
        print(f"\n4️⃣ Getting updated user information...")
        updated_users = conn.proxmox.access.users.get()
        updated_test_user = None
        for user in updated_users:
            if user.get('userid') == userid:
                updated_test_user = user
                break

        if updated_test_user:
            print("✅ Updated user info:")
            pprint(updated_test_user)

        return updated_test_user

    except Exception as e:
        print(f"❌ Debug error: {e}")
        return None

# Global connection for interactive use
conn = None

def main():
    """Main function for interactive setup"""
    global conn

    print("🚀 Interactive Proxmox Development Session")
    print("=" * 50)

    # Setup connection
    conn = setup_connection()

    if conn:
        # Show version info
        version_info = conn.get_version_info()
        print(f"\n📊 Version Info: {version_info}")

        # Show available functions
        explore_api(conn)

        print(f"\n🎯 Connection is ready!")
        print("Use 'conn' variable for API calls")
        print("Use debug_user_operations(conn) for step-by-step debugging")
        print("Use pprint() for better output formatting")

    return conn

if __name__ == "__main__":
    # Run setup and start interactive session
    conn = main()

    # For Python -i mode, these will be available
    print(f"\n💡 Starting interactive mode...")
    print("Available variables: conn, debug_user_operations, explore_api")
EOF
```

#### Step 2: Start Interactive Session
```bash
cd /Users/gkorkmaz/Projects/dev/ansible_development/roles/role_proxmox/tests

# Start interactive Python with setup
python3 -i interactive_debug.py
```

#### Step 3: Interactive Commands
Once in the Python interactive session:

```python
# Basic API exploration
>>> conn.proxmox.version.get()
>>> pprint(conn.get_version_info())

# Explore users
>>> users = conn.proxmox.access.users.get()
>>> print(f"Found {len(users)} users")
>>> pprint(users[0])  # Show first user

# Debug step by step
>>> debug_user_operations(conn, "my-test-user@pve")

# Test specific API calls
>>> try:
...     result = conn.proxmox.access.users.post(
...         userid="test@pve",
...         password="pass123"
...     )
...     print("Success:", result)
... except Exception as e:
...     print("Error:", e)

# Explore storage
>>> storages = conn.proxmox.storage.get()
>>> for storage in storages:
...     print(f"{storage['storage']}: {storage['type']}")

# Test feature detection
>>> for feature in ['api_tokens', 'user_groups', 'vm_templates']:
...     supported = conn.api_compat.is_feature_supported(feature)
...     print(f"{feature}: {'✅' if supported else '❌'}")

# Exit interactive mode
>>> exit()
```

#### Step 4: Advanced Debugging Session
```bash
cat > advanced_debug.py << 'EOF'
#!/usr/bin/env python3
"""
Advanced debugging with logging and error handling
"""

import sys
import os
import logging
import json
from pprint import pprint

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/proxmox_debug.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Add module paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'module_utils'))

def setup_debug_connection():
    """Setup connection with debug logging"""
    from pve_api_compatibility import CompatibleProxmoxConnection

    # Enable proxmoxer debugging
    import proxmoxer.core
    proxmoxer.core.logger.setLevel(logging.DEBUG)

    config = {
        'host': 'your-proxmox-host.com',
        'user': 'root@pam',
        'password': 'your-password',
        'verify_ssl': False
    }

    logger.info("Setting up debug connection...")
    conn = CompatibleProxmoxConnection(**config)

    if conn.test_connection():
        logger.info("✅ Debug connection successful!")
        return conn
    else:
        logger.error("❌ Debug connection failed!")
        return None

def trace_api_call(conn, endpoint, method='get', **kwargs):
    """Trace a specific API call with full logging"""
    logger.info(f"🔍 Tracing API call: {method.upper()} {endpoint}")

    try:
        # Navigate to endpoint
        api_obj = conn.proxmox
        for part in endpoint.split('.'):
            api_obj = getattr(api_obj, part)

        # Make call
        method_func = getattr(api_obj, method)
        result = method_func(**kwargs)

        logger.info(f"✅ API call successful")
        logger.debug(f"Result: {json.dumps(result, indent=2, default=str)}")

        return result
    except Exception as e:
        logger.error(f"❌ API call failed: {e}")
        raise

if __name__ == "__main__":
    print("🔬 Advanced Debug Session")
    print("Check /tmp/proxmox_debug.log for detailed logs")

    conn = setup_debug_connection()

    if conn:
        print("Debug connection ready!")
        print("Use trace_api_call(conn, 'access.users') to trace calls")
EOF

# Run advanced debug
python3 -i advanced_debug.py

# In another terminal, watch the logs
tail -f /tmp/proxmox_debug.log
```

---

## 4. Common Debugging Patterns

### Error Handling Patterns
```python
# Pattern 1: Try-catch with detailed logging
try:
    result = conn.proxmox.access.users.get()
    logger.info(f"Success: {len(result)} users found")
except Exception as e:
    logger.error(f"Failed to get users: {e}")
    logger.error(f"Exception type: {type(e).__name__}")
    if hasattr(e, 'status_code'):
        logger.error(f"HTTP Status: {e.status_code}")

# Pattern 2: API version fallback testing
def test_with_fallback(conn):
    try:
        # Try modern API
        result = conn.proxmox.some.new.endpoint.get()
    except Exception as e:
        if 'not found' in str(e).lower():
            # Try legacy API
            result = conn.proxmox.some.old.endpoint.get()
        else:
            raise e
    return result

# Pattern 3: Parameter validation
def validate_params(params):
    required = ['userid', 'password']
    missing = [p for p in required if not params.get(p)]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
```

### Testing Workflows
```bash
# Quick module syntax check
python3 -m py_compile library/pve_configure_users.py
python3 -m py_compile library/pve_configure_storage.py

# Test module import
python3 -c "
import sys; sys.path.insert(0, 'library')
import pve_configure_users
import pve_configure_storage
print('All modules imported successfully')
"

# Quick CLI test (on Proxmox host)
python3 -c "
import sys; sys.path.insert(0, 'module_utils')
from pve_base_utils import get_proxmox_data
data = get_proxmox_data()
print('CLI working, found', len(data['users']), 'users')
"

# Quick proxmoxer test (if available)
python3 -c "
import sys; sys.path.insert(0, 'module_utils')
try:
    from pve_api_compatibility import CompatibleProxmoxConnection
    print('Proxmoxer compatibility available')
except ImportError:
    print('Proxmoxer not available')
"

# Module execution test
ansible localhost -m pve_configure_users -a "desired_users=[]" -vvv
ansible localhost -m pve_get_tokens -a "token_file=/etc/pve/priv/token.cfg" -vvv
```

---

## 5. Troubleshooting

### Common Issues and Solutions

#### Import Errors
```bash
# Problem: Module not found
# Solution: Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Add correct path
export PYTHONPATH="/Users/gkorkmaz/Projects/dev/ansible_development/roles/role_proxmox/module_utils:$PYTHONPATH"
```

#### Connection Issues
```python
# Debug connection step by step
import proxmoxer
from proxmoxer.core import ProxmoxAPIException

try:
    api = proxmoxer.ProxmoxAPI('host', user='user', password='pass', verify_ssl=False)
    print("Basic connection works")

    version = api.version.get()
    print(f"Version: {version}")

except ProxmoxAPIException as e:
    print(f"API Error: {e}")
    print(f"Status: {e.status_code}")
except Exception as e:
    print(f"Connection Error: {e}")
```

#### Module Development Issues
```bash
# Check Ansible can find your module
ansible-doc -t module your_module_name

# Validate module structure
python3 library/your_module.py --help

# Test module directly
python3 library/your_module.py <<EOF
{
    "ANSIBLE_MODULE_ARGS": {
        "param1": "value1",
        "param2": "value2"
    }
}
EOF
```

### Debugging Checklist

1. **Connection**: Can you connect to Proxmox API?
2. **Authentication**: Are credentials correct?
3. **Permissions**: Does user have required permissions?
4. **API Version**: Is the endpoint supported in this version?
5. **Parameters**: Are all required parameters provided?
6. **Network**: Are there firewall/network issues?
7. **SSL**: Are SSL certificate issues causing problems?

### Log Locations
- **Ansible logs**: Use `-vvv` for verbose output
- **Custom logs**: `/tmp/proxmox_debug.log` (if configured)
- **System logs**: `/var/log/messages` or `journalctl`
- **Proxmox logs**: On Proxmox server `/var/log/pveproxy/access.log`

---

## Quick Reference Commands

```bash
# Python CLI Testing
python3 tests/python_cli/test_cli_modules.py

# Test specific modules
python3 tests/python_cli/test_user_module.py

# Ansible Module Testing
ansible-playbook tests/ansible/test_basic.yml -vvv

# Interactive Debugging
python3 -i tests/interactive_debug.py

# Check module syntax
python3 -m py_compile library/pve_configure_users.py
python3 -m py_compile library/pve_configure_storage.py

# Test single module
ansible localhost -m pve_configure_users -a "desired_users=[]" -vvv
ansible localhost -m pve_get_tokens -a "token_file=/etc/pve/priv/token.cfg" -vvv

# Watch debug logs
tail -f /tmp/proxmox_debug.log

# Validate Ansible modules
ansible-doc -t module pve_configure_users
ansible-doc -t module pve_configure_storage
```

This guide provides comprehensive testing strategies for all phases of Ansible module development. Use the appropriate method based on your current development needs.
