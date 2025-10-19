# Proxmox Role Configuration Variables
## User Configuration Variables

```yaml
proxmox_users:
  - username: string       # Required: Username for Proxmox account
    password: string       # Optional: User password
    email: string          # Optional: User email address
    firstname: string      # Optional: User first name
    lastname: string       # Optional: User last name
    enable: boolean        # Optional: Enable/disable user account (default: true)
    expire: integer        # Optional: Account expiration timestamp
    groups:                # Optional: List of groups user belongs to
      - string
    permissions:           # Optional: User-specific permissions
      - path: string       # Required: Permission path (e.g., /, /vms, /storage)
        roles:             # Required: List of roles for this path
          - string         # Example: Administrator, PVEVMAdmin, PVEDatastoreUser
    tokens:                # Optional: API tokens for user
      - name: string       # Required: Token name
        comment: string    # Optional: Token description
        expire: integer    # Optional: Token expiration timestamp
        privsep: boolean   # Optional: Privilege separation
```

## Group Configuration Variables
```yaml
proxmox_groups:
  - name: string           # Required: Group name
    comment: string        # Optional: Group description
    members:               # Optional: List of group members
      - string             # Username of group member
    permissions:           # Optional: Group-level permissions
      - path: string       # Required: Permission path
        roles:             # Required: List of roles
          - string         # Role names
```

## Storage Configuration Variables

```yaml
proxmox_storage:
  - name: string           # Required: Storage name
    type: string           # Required: Storage type (dir, nfs, cifs, rbd, zfspool, lvmthin, iscsi, glusterfs, cephfs)
    path: string           # Required for most types: Storage path
    content:               # Required: List of allowed content types
      - images             # VM disk images
      - rootdir            # Container templates
      - backup             # Backup files
      - iso                # ISO files
      - snippets           # Snippet files
      - vztmpl             # Container templates

    # Type-specific options
    server: string         # NFS/CIFS: Server hostname/IP
    export: string         # NFS: Export path
    share: string          # CIFS: Share name
    username: string       # CIFS: Username
    password: string       # CIFS: Password

    # Common options
    maxfiles: integer      # Optional: Maximum number of files
    prune_backups: string  # Optional: Backup retention policy
    shared: boolean        # Optional: Mark storage as shared
    disable: boolean       # Optional: Disable storage
    nodes: string          # Optional: Nodes that can access this storage
```

## Network Configuration Variables

```yaml
proxmox_networks:
  - name: vmbr0            # Required: Bridge name
    type: bridge           # Required: Network type (bridge, bond, etc)
    address: 192.168.1.1   # Optional: IP address
    netmask: 255.255.255.0 # Optional: Network mask
    gateway: 192.168.1.254 # Optional: Gateway address
    autostart: true        # Optional: Start on boot
    ports:                 # Optional: Physical ports for bridge/bond
      - eno1
      - eno2
    bond_mode: balance-rr  # Optional: Bond mode
    vlan_aware: true       # Optional: Enable VLAN awareness
    mtu: 1500              # Optional: MTU size
```

## Volume Configuration Variables

```yaml
proxmox_volumes:
  - name: local-lvm        # Required: Volume name
    type: lvmthin          # Required: Volume type (lvm, lvmthin, zfs)
    device: /dev/sda       # Required: Device path
    vgname: pve            # Required for LVM: Volume group name
    thinpool: data         # Required for LVMthin: Thin pool name
    size: 500G             # Optional: Volume size
    shared: true           # Optional: Mark as shared
    nodes:                 # Optional: Allowed nodes
      - pve1
      - pve2

  - name: zfs-storage
    type: zfspool
    device: /dev/sdb
    raidlevel: mirror      # ZFS specific: RAID level
    ashift: 12             # ZFS specific: Sector size
    compression: lz4       # ZFS specific: Compression algorithm
```

# Complete Example with Network and Volume Configuration
```yaml
- hosts: proxmox
  vars:
    proxmox_networks:
      - name: vmbr0
        type: bridge
        address: 10.0.0.1
        netmask: 255.255.255.0
        gateway: 10.0.0.254
        ports:
          - eno1
        autostart: true

      - name: bond0
        type: bond
        ports:
          - eno2
          - eno3
        bond_mode: balance-alb

    proxmox_volumes:
      - name: local-lvm
        type: lvmthin
        device: /dev/sda3
        vgname: pve
        thinpool: data
        size: 1T

      - name: backup-storage
        type: zfspool
        device: /dev/sdb
        raidlevel: mirror
        compression: lz4
```

# Example Full Configuration

```yaml
proxmox_users:
  - username: admin
    password: "secure123"
    email: "admin@domain.com"
    firstname: "System"
    lastname: "Administrator"
    enable: true
    groups:
      - administrators
    permissions:
      - path: /
        roles: ['Administrator']
    tokens:
      - name: backup-token
        comment: "Automated backup system"
        expire: 1735689600
        privsep: true

proxmox_groups:
  - name: developers
    comment: "Development team access"
    members:
      - dev1
      - dev2
    permissions:
      - path: /vms
        roles: ['PVEVMAdmin']
      - path: /storage/backup
        roles: ['PVEDatastoreUser']

proxmox_storage:
  - name: local-backup
    type: dir
    path: /mnt/backup
    content:
      - backup
      - iso
      - vztmpl
    maxfiles: 1000
    prune_backups: "keep-last=5,keep-hourly=24,keep-daily=7,keep-weekly=4,keep-monthly=12"
    shared: true
```

# ISO Image Management Configuration

```yaml
proxmox_iso_downloads:
  - name: "ubuntu-22.04-live-server-amd64.iso"                                      # Required: ISO filename
    url: "https://releases.ubuntu.com/22.04/ubuntu-22.04.3-live-server-amd64.iso"   # Required: Download URL

  - name: "debian-12.1.0-amd64-netinst.iso"
    url: "https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-12.1.0-amd64-netinst.iso"
```
