# Postmortem: root locked out of OpenLDAP `cn=config` by `olcSecurity: tls=1`

| | |
|---|---|
| **Date** | 2026-10-30 (latent since 2026-10-29) |
| **Severity** | Medium (no user impact, but configuration changes were impossible while slapd ran) |
| **Affected host** | db01 (192.168.196.12) — OpenLDAP 2.6 |
| **Detected by** | Ansible dry run (`ansible-playbook playbooks/ldap.yml --check --diff`) |
| **Author** | SitKevin |

## Summary

In Phase 2 (step 5.7) slapd was hardened with `olcSecurity: tls=1` to refuse unencrypted binds. While writing the Ansible `openldap` role in Phase 3, the dry run failed on the first `cn=config` task:

```
Cannot bind to the server.
{'result': 13, 'desc': 'Confidentiality required', 'info': 'TLS confidentiality required'}
```

The role connects like an administrator does: `ldapi:///` (local Unix socket) with SASL EXTERNAL as root. That connection was now rejected — **nobody, including root, could change `cn=config` while slapd was running.** Users and Gitea were unaffected (they use StartTLS).

## Root cause

`tls=<n>` requires a **TLS layer** of at least `n` bits. The local `ldapi:///` socket is secure because it never leaves the machine, but it has no TLS layer, so its TLS strength factor is 0 → rejected.

`ssf=<n>` is the **overall** security strength factor of the connection:

| Connection | ssf | `tls=1` | `ssf=1` |
|---|---|---|---|
| Network, plain | 0 | rejected | rejected |
| Network, StartTLS | ≥ 128 | allowed | allowed |
| Local `ldapi:///` | 71 (`olcLocalSSF`) | **rejected** | allowed |

The Phase 2 tests only checked the *user* path (plain bind rejected, `-ZZ` bind accepted). The *admin* path (`-Y EXTERNAL -H ldapi:///`) was never re-tested after the change.

## Timeline

| Time (UTC+7) | Event |
|---|---|
| 10-29 ~11:10 | `olcSecurity: tls=1` applied (Phase 2, step 5.7); user-path tests pass |
| 10-30 14:08 | Ansible `--check` fails with `Confidentiality required (13)` on `cn=config` |
| 14:09 | Confirmed manually: `sudo ldapwhoami -Q -Y EXTERNAL -H ldapi:///` → error 13 |
| 14:10 | VMware snapshot `before-ldap-ssf-fix`; slapd stopped; fixed offline |
| 14:12 | slapd running, all 4 checks pass |

## Resolution

`cn=config` can't be changed online, so it was changed **offline**:

```bash
sudo systemctl stop slapd
cat > /tmp/ssf.ldif <<'LDIF'
dn: cn=config
changetype: modify
replace: olcSecurity
olcSecurity: ssf=1
LDIF
sudo -u openldap slapmodify -n0 -F /etc/ldap/slapd.d -l /tmp/ssf.ldif   # as openldap: keep file ownership
sudo systemctl start slapd
```

Verification:

| Check | Expected | Result |
|---|---|---|
| `sudo ldapwhoami -Q -Y EXTERNAL -H ldapi:///` | admin path works | ✅ `dn:gidNumber=0+uidNumber=0,...` |
| `ldapsearch ... -b cn=config olcSecurity` | `ssf=1` | ✅ |
| Plain network bind (`ldapwhoami -x -H ldap://db01...`) | still rejected | ✅ `Confidentiality required (13)` |
| StartTLS bind (`-ZZ`) | works | ✅ |

## What went well

- The **dry run** caught it before any change was made by the role.
- A VMware snapshot was taken before the offline edit.
- `slapmodify` ran as `openldap`, so config file ownership stayed correct and slapd started first time.

## Lessons

- After tightening security, **re-test the administration path**, not only the user path.
- Prefer the setting that expresses the real requirement: "no plaintext over the network" = `ssf=1`, not "TLS everywhere" = `tls=1`.

## Action items

- [x] `olcSecurity: ssf=1` on db01
- [x] Repo: `configs/ldap/tls.ldif`, Ansible role `openldap`, `docs/phase2-services.md` updated
- [x] Admin-path check (`sudo ldapwhoami -Q -Y EXTERNAL -H ldapi:///`) added to the [user-management runbook](../runbooks/user-management.md#health-check-after-any-ldap-change)
