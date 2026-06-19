
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

## Docker Compose fix v2 - microservizi realmente collegati

Questa versione corregge `docker-compose.yml` per Windows/Docker Desktop:

- nomi servizi Docker coerenti con gli URL del Gateway: `auth-service`, `tenant-service`, `focus-service`, `wellness-service`, `passport-service`, `billing-service`, `compliance-service`, `locker-service`, `registry-service`;
- rete Docker dedicata `focus360-net`;
- healthcheck per tutti i microservizi;
- Gateway esposto su `http://localhost:8080`;
- microservizi esposti anche su porte locali per debug: `8001-8009`;
- nuovo endpoint Gateway: `/health/services` per verificare la raggiungibilità reale interna.

### Avvio su Windows PowerShell

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Apri:

- `http://localhost:8080`
- `http://localhost:8080/health`
- `http://localhost:8080/health/services`

### Test rapido

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\check_microservices.ps1
```

Se vuoi controllare un servizio singolo:

- Auth: `http://localhost:8001/health`
- Tenant: `http://localhost:8002/health`
- Focus: `http://localhost:8003/health`
- Wellness: `http://localhost:8004/health`
- Passport: `http://localhost:8005/health`
- Billing: `http://localhost:8006/health`
- Compliance: `http://localhost:8007/health`
- Locker: `http://localhost:8008/health`
- Registry: `http://localhost:8009/health`


## Frontend-Service Bootstrap collegato al Gateway

Questa build integra il monolite `legacy_alpha_monolith` come `frontend-service`, pensato per demo commerciali e scuole pilota.

### Avvio locale completo
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

URL:
- Gateway: http://localhost:8080
- Frontend webapp: http://localhost:8090
- Stato servizi: http://localhost:8080/health/services
- Stato Gateway dal frontend: http://localhost:8090/system-status

### Deploy Render multi-servizio
Creare un ulteriore Web Service Render:
- Name: `focus360-frontend-service`
- Root Directory: `frontend-service`
- Environment: Docker
- Dockerfile Path: `Dockerfile`
- Env `GATEWAY_URL`: URL del gateway Render

Nel Gateway impostare anche:
```env
FRONTEND_URL=https://focus360-frontend-service.onrender.com
FRONTEND_PUBLIC_URL=https://focus360-frontend-service.onrender.com
```
