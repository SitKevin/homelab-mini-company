# Ansible

Run everything from the **bastion**, inside this directory:

```bash
cd ~/homelab-mini-company/ansible
ansible all --list-hosts           # what's in the inventory
ansible homelab -m ping            # SSH + Python on every node
ansible-playbook playbooks/ping.yml -K   # -K = ask sudo password
```

| Path | Purpose |
|---|---|
| `ansible.cfg` | Defaults (inventory path, remote user, SSH pipelining) |
| `inventory/hosts.ini` | Hosts and groups: `bastion`, `web`, `db`, `monitoring`, `homelab` (all) |
| `group_vars/all.yml` | Variables shared by all hosts |
| `playbooks/` | Playbooks |
| `roles/` | Roles (common, bind9, postgresql, gitea, nginx, openldap) — Phase 3 |
