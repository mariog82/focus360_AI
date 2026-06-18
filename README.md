
# Focus360 AI Enterprise Alpha - Microservices SaaS DevSecOps

Questa versione riorganizza la Alpha `focus360_ai_enterprise_alpha_lockers_api_registro.zip` in architettura SaaS a microservizi.

## Avvio rapido
```bash
pip install -r requirements.txt
./scripts/run_tests.sh
./scripts/devsecops_scan.sh
```

## Avvio con Docker Compose
```bash
docker compose up --build
```
Gateway: `http://localhost:8080/health`

## Microservizi
- gateway
- auth-service
- tenant-service
- focus-service
- wellness-service
- passport-service
- locker-service
- registry-service
- billing-service
- compliance-service

## DevSecOps
Sono inclusi test di integrazione, sistema, accettazione e sicurezza, più script SAST/dependency checking. La cartella `legacy_alpha_monolith` contiene la versione monolitica originale di riferimento.

## Note produzione
Questa è una base architetturale eseguibile/prototipale. Per produzione servono PostgreSQL, gestione segreti, HTTPS obbligatorio, logging centralizzato, backup, DPIA, DPA, privacy policy, hardening container, WAF e monitoraggio.
