#!/usr/bin/python

DEFAULT_STORAGE_CONFIG = '/etc/pve/storage.cfg'

def parse_storage_config(content):
    storages = []
    current_storage = None
    
    for line in content.splitlines():
        line = line.rstrip()
        if not line:
            continue
            
        if line.startswith('dir:'):
            if current_storage:
                storages.append(current_storage)
            
            storage_name = line.split(':', 1)[1].strip()
            current_storage = {
                'name': storage_name,
                'type': 'dir',
                'path': None,
                'content': None,
                'prune_backups': None
            }
        elif line.strip().startswith('path'):
            current_storage['path'] = line.strip().split(' ', 1)[1]
        elif line.strip().startswith('content'):
            current_storage['content'] = line.strip().split(' ', 1)[1].split(',')
        elif line.strip().startswith('prune-backups'):
            current_storage['prune_backups'] = line.strip().split(' ', 1)[1]
    
    if current_storage:
        storages.append(current_storage)
    
    return storages

def read_storage_config(config_file=None):
    """
    Read and parse storage configuration from file
    
    Args:
        config_file (str): Optional path to storage config file
        
    Returns:
        list: Parsed storage configurations
    """
    storage_file = config_file or DEFAULT_STORAGE_CONFIG
    
    try:
        with open(storage_file, 'r') as f:
            content = f.read()
        return parse_storage_config(content)
    except Exception as e:
        raise Exception(f"Failed to read storage config from {storage_file}: {str(e)}")
