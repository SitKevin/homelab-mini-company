# Gitea → LDAP authentication source

Site Administration → Identity & Access → Authentication Sources → Add
(direct URL: `https://git.sitkevin.duckdns.org/-/admin/auths`)

| Field | Value |
|---|---|
| Authentication Type | LDAP (via BindDN) |
| Authentication Name | `homelab-ldap` |
| Security Protocol | **StartTLS** |
| Host / Port | `db01.homelab.internal` / `389` |
| Bind DN | `cn=gitea,ou=services,dc=homelab,dc=internal` |
| Bind Password | *(password manager / Ansible Vault)* |
| User Search Base | `ou=people,dc=homelab,dc=internal` |
| User Filter | `(&(objectClass=inetOrgPerson)(uid=%[1]s))` |
| Admin Filter | `(uid=an)` |
| Restricted Filter | *(empty)* |
| Username / First name / Surname / Email attribute | `uid` / `givenName` / `sn` / `mail` |
| Skip TLS Verify | **off** (web01 trusts `homelab-ca.crt`) |
| Enable LDAP Groups | on |
| Group Search Base DN | `ou=groups,dc=homelab,dc=internal` |
| Group Attribute Containing List Of Users | `member` |
| User Attribute Listed In Group | `dn` |
| Verify group membership in LDAP | `(cn=staff)` → only employees can log in |
| Enable User Synchronization | on (users removed from LDAP get deactivated) |
| Allow an empty search result to deactivate all users | **off** (an LDAP outage must not lock everyone out) |

On web01 the CA must be trusted first:
```bash
sudo cp homelab-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates
ldapwhoami -x -ZZ -H ldap://db01.homelab.internal -D "cn=gitea,ou=services,dc=homelab,dc=internal" -W
```
