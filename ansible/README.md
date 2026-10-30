# Ansible

Run everything from the **bastion**, inside this directory:

```bash
cd ~/homelab-mini-company/ansible
ansible-playbook site.yml --check --diff   # dry run: what WOULD change on every host
ansible-playbook site.yml                  # build / converge the whole homelab

ansible all --list-hosts                   # what's in the inventory
ansible homelab -m ping                    # SSH + Python on every node
ansible-playbook playbooks/web.yml         # one tier only (common, dns, db, ldap, web, maintenance)
```

`site.yml` runs the tiers in dependency order: **common** (all hosts) → **dns** (bastion) → **db** → **ldap** (db01) → **web** (web01) → **maintenance** (all). Every role is idempotent: a second run reports `changed=0`.

| Path | Purpose |
|---|---|
| `ansible.cfg` | Defaults (inventory path, remote user, SSH pipelining, `become_exe = sudo.ws` for Ubuntu 26.04) |
| `inventory/hosts.ini` | Hosts and groups: `jumphost`, `web`, `db`, `monitoring`, `homelab` (all) |
| `inventory/group_vars/all/vars.yml` | Variables shared by all hosts |
| `inventory/group_vars/all/vault.yml` | Secrets, encrypted with Ansible Vault (`vault_*` variables) |
| `inventory/host_vars/<host>.yml` | Per-host variables (e.g. `ufw_rules`) |
| `site.yml` | Entry point: imports every playbook in dependency order |
| `playbooks/` | One playbook per tier: `common`, `dns`, `db`, `ldap`, `web` (+ `ping`) |
| `roles/` | `common`, `bind9`, `postgresql`, `openldap`, `gitea`, `nginx` |

> `group_vars/` and `host_vars/` must sit next to the inventory file (or the playbook) — Ansible doesn't look anywhere else.

## Secrets (Ansible Vault)

- Vault password: `~/.ansible/vault_pass` on the bastion (`chmod 600`, **not** in the repo, backed up in a password manager).
- Secrets: `inventory/group_vars/all/vault.yml`, AES-256 encrypted, safe to commit.
- Naming: secrets are `vault_*` in `vault.yml`; `vars.yml` references them (e.g. `ansible_become_password: "{{ vault_become_password }}"`), so you can see which variables are secret without decrypting.

```bash
ansible-vault view inventory/group_vars/all/vault.yml   # read
ansible-vault edit inventory/group_vars/all/vault.yml   # change / add secrets
```
