
# Piano DevSecOps

## Controlli implementati nello scaffold
- SAST: Bandit.
- Dependency checking: pip-audit.
- Test sicurezza: accesso locker protetto, password hashing.
- Pipeline CI: GitHub Actions.
- Containerizzazione: Dockerfile per microservizio e docker-compose.

## Controlli da eseguire in staging/prod
- DAST con OWASP ZAP.
- Container/image scanning con Trivy o Grype.
- Secret scanning con Gitleaks.
- Penetration test autenticato annuale e dopo major release.
- Vulnerability management con SLA: Critical 72h, High 7gg, Medium 30gg.
