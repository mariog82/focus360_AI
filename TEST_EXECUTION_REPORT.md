# Test Execution Report

## Ambiente sandbox
- Controllo sintattico Python: eseguito con `python -m compileall gateway services shared`.
- Esito: OK.

## Test applicativi
Sono inclusi script e suite pytest per:
- test di integrazione;
- test di sistema;
- test di accettazione;
- test di sicurezza.

Nel sandbox corrente non sono installati Flask/Flask-SQLAlchemy/Werkzeug; quindi l'esecuzione completa della suite `pytest` richiede prima:

```bash
pip install -r requirements.txt
./scripts/run_tests.sh
```

## DevSecOps
Sono inclusi script per SAST e dependency checking:

```bash
./scripts/devsecops_scan.sh
```

Per produzione si raccomanda di aggiungere:
- Trivy/Grype per container scanning;
- OWASP ZAP per DAST;
- Gitleaks per secret scanning;
- SBOM CycloneDX;
- penetration test autenticato su ambiente staging.
