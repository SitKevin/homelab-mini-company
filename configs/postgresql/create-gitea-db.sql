-- db01: run with  sudo -u postgres psql
-- Creates an empty database + a dedicated, non-superuser role for Gitea.
-- Gitea creates its own tables (migrations) on first start.
-- Generate the password with:  openssl rand -base64 24
-- NEVER commit the real password - it lives in a password manager
-- (and in Ansible Vault from Phase 3).

CREATE ROLE gitea WITH LOGIN PASSWORD 'CHANGE_ME';

-- template0 + explicit UTF8 is what the Gitea docs recommend
-- (avoids encoding problems with non-ASCII repo names / commit messages).
CREATE DATABASE gitea WITH OWNER gitea TEMPLATE template0
  ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8';

-- If en_US.UTF-8 is missing:  sudo locale-gen en_US.UTF-8 && sudo systemctl restart postgresql
