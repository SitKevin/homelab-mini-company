# Runbook — Employee accounts (LDAP)

Accounts live in OpenLDAP on db01 (`dc=homelab,dc=internal`). Gitea authenticates against it and only lets in members of `cn=staff`. **Ansible is the source of truth** for users and group membership: [`ansible/roles/openldap/defaults/main.yml`](../../ansible/roles/openldap/defaults/main.yml).

## Onboarding — new employee

1. Add the user (and groups) in `ldap_users` / `ldap_groups`:

   ```yaml
   ldap_users:
     - { uid: hoa, cn: Vo Thi Hoa, sn: Vo, givenName: Hoa }
   ldap_groups:
     - { cn: staff, description: All employees, members: [an, binh, chi, dung, hoa] }
     - { cn: dev,   description: Developers,    members: [binh, chi, hoa] }
   ```

2. Apply (dry run first):

   ```bash
   cd ~/homelab-mini-company/ansible
   ansible-playbook playbooks/ldap.yml --check --diff
   ansible-playbook playbooks/ldap.yml
   ```

   A **new** user gets the initial password from Vault (`vault_ldap_initial_user_password`); existing users' passwords are never touched.
3. The Gitea account is created automatically at the first login.
4. Commit and push the change.

## Offboarding — employee leaves

1. Remove the uid from **every** group in `ldap_groups` (membership is enforced exactly) and apply `playbooks/ldap.yml`.
2. Result: Gitea refuses the next login (the auth source only accepts members of `cn=staff`).
3. Optionally delete the LDAP entry later (after reassigning their repositories).

## Reset a user's password

```bash
# db01 (admin password: ansible-vault view inventory/group_vars/all/vault.yml)
ldappasswd -x -ZZ -H ldap://db01.homelab.internal -D "cn=admin,dc=homelab,dc=internal" -W -S "uid=<uid>,ou=people,dc=homelab,dc=internal"
```

Users can change their own password (`by self write` in the ACL).

## Reset the LDAP admin password (lost)

Root on db01 can always change the configuration over the local socket (SASL EXTERNAL), without the LDAP password:

```bash
slappasswd                                    # prints {SSHA}... for the new password
cat > /tmp/rootpw.ldif <<'EOF'
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcRootPW
olcRootPW: {SSHA}...
EOF
sudo ldapmodify -Q -Y EXTERNAL -H ldapi:/// -f /tmp/rootpw.ldif && rm /tmp/rootpw.ldif
```

Then update `vault_ldap_admin_password`.

## Health check after any LDAP change

```bash
sudo ldapwhoami -Q -Y EXTERNAL -H ldapi:///                       # admin path (root over the socket) works
ldapwhoami -x -H ldap://db01.homelab.internal -D "uid=binh,ou=people,dc=homelab,dc=internal" -W
                                                                   # plain network bind -> must FAIL (13)
ldapwhoami -x -ZZ -H ldap://db01.homelab.internal -D "uid=binh,ou=people,dc=homelab,dc=internal" -W
                                                                   # StartTLS bind -> must work
```

The first check exists because of the [2026-10-30 postmortem](../postmortems/2026-10-30-ldap-cn-config-lockout.md): a security setting once locked root out of `cn=config`.
