# ISIP — Security Intelligence Platform

Evidence-first web OSINT workspace for authorized security research and institutional incident response.

## Safety
ISIP analyzes public sources and operator-provided evidence. It does not retrieve hidden emails, login IPs, device identifiers, GPS, credentials, or private content; bypass platform controls; or automate authenticated Instagram scraping. Username matches are unverified leads, not proof of common ownership.

## Quick start
1. Copy `.env.example` to `.env`.
2. Set a unique `APP_SECRET_KEY` (32+ characters) and strong `ADMIN_PASSWORD` (14+ characters).
3. Run `docker compose up --build -d`.
4. Open http://localhost:8000.

This MVP uses SQLite and local evidence storage. Keep it bound to localhost until HTTPS and deployment hardening are configured.

## Features
- Case management with authorization and scope
- Evidence upload with SHA-256 hash and timestamp
- Sherlock public username presence checks in a worker
- ExifTool available in worker image
- Optional urlscan.io submission with explicit confirmation
- Audit trail, JSON report, dark dashboard

## API
- `GET /api/health`
- `POST /api/login`, `POST /api/logout`
- `GET /api/cases`, `POST /api/cases`
- `POST /api/cases/{id}/evidence`
- `POST /api/cases/{id}/username-check`
- `POST /api/cases/{id}/url-check`
- `GET /api/cases/{id}/findings`, `GET /api/cases/{id}/report`

All routes except health and login require a session.

## Deployment
Use HTTPS, change secrets, restrict access, encrypt backups, configure evidence retention, and review third-party disclosure before enabling urlscan. This is an MVP starter, not a production-certified investigation suite.

## Topology diagrams
See [the topology guide](docs/topologies.md) for the logical architecture, Docker deployment, isolated experimental network, evidence workflow, and a suggested test matrix.

![ISIP logical architecture](docs/topology-architecture.svg)
