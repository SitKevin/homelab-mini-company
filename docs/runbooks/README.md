# Runbooks

Step-by-step procedures for operating the homelab.

| Runbook | When |
|---|---|
| [alerts.md](alerts.md) | A Discord alert fired — what to check for each of the 9 alerts |
| [restore.md](restore.md) | Data is lost or corrupted — restore Gitea, PostgreSQL or LDAP from restic |
| [user-management.md](user-management.md) | Onboarding / offboarding an employee, password resets, LDAP admin password recovery |

Routine operations (from the bastion, `~/homelab-mini-company/ansible`):

```bash
ansible-playbook site.yml --check --diff     # what would change anywhere
ansible-playbook site.yml                    # converge everything
ansible-playbook playbooks/<tier>.yml        # one tier: common, dns, db, ldap, web, maintenance, monitoring, backup
```
