#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r"""
---
module: pve_get_tokens
short_description: Retrieves Proxmox VE API tokens
description:
    - Reads and parses API tokens from token.cfg
    - Displays token IDs and their values
    - Maps tokens to their respective users
version_added: "1.0"
options:
    token_file:
        description:
            - Path to Proxmox token configuration file
        default: /etc/pve/priv/token.cfg
        type: str
"""

import os

from ansible.module_utils.basic import AnsibleModule


class TokenReader:
    def __init__(self, token_file):
        self.token_file = token_file
        self.tokens = []

    def read_tokens(self):
        try:
            with open(self.token_file, "r") as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    token_id, token_value = line.split(" ", 1)
                    user, token_name = token_id.split("!", 1)
                    self.tokens.append(
                        {
                            "user": user,
                            "token_name": token_name,
                            "token_id": token_id,
                            "token_value": token_value,
                        }
                    )

            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            raise Exception(f"Failed to read tokens: {str(e)}")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            token_file=dict(type="str", default="/etc/pve/priv/token.cfg")
        )
    )

    try:
        reader = TokenReader(module.params["token_file"])
        if reader.read_tokens():
            module.exit_json(changed=False, tokens=reader.tokens)
        else:
            module.fail_json(msg="Token configuration file not found")
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == "__main__":
    main()
