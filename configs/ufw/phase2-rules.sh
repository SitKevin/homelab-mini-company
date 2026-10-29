#!/usr/bin/env bash
# Phase 2 firewall rules (on top of Phase 1: default deny incoming, allow SSH).
# Run the block for the host you are on - check the prompt first!

# --- db01 ---------------------------------------------------------------
# PostgreSQL only from web01 (second layer next to pg_hba.conf)
# sudo ufw allow from 192.168.196.11 to any port 5432 proto tcp comment 'postgres from web01'
# LDAP (StartTLS on 389) only from web01 - Gitea authentication
# sudo ufw allow from 192.168.196.11 to any port 389 proto tcp comment 'ldap from web01'

# --- web01 --------------------------------------------------------------
# HTTP + HTTPS for Nginx. Port 3000 (Gitea) is intentionally NOT opened.
# sudo ufw allow 'Nginx Full' comment 'HTTP/HTTPS'

# Verify
# sudo ufw status verbose
