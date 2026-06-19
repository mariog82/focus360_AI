# Focus360 AI - Fix deploy Render multi-servizio

## Errore risolto

Errore:

```text
failed to calculate checksum ... "/services/auth_service": not found
```

Causa: su Render è stato probabilmente impostato `Root Directory = services/auth_service` mentre il Dockerfile del microservizio si aspetta come build context la root del progetto, perché deve copiare anche `shared/` e `requirements.txt`.

## Regola corretta

Per ogni servizio Render:

- Repository: repository GitHub del progetto
- Branch: main
- Root Directory: lasciare vuoto se il progetto è alla root del repository
- se il repository contiene una cartella `focus360_microservices_alpha`, allora Root Directory deve essere `focus360_microservices_alpha`
- Environment: Docker
- Dockerfile Path: usare il Dockerfile root dedicato, ad esempio `Dockerfile.auth_service`

## Servizi da creare

### Gateway pubblico

- Name: `focus360-gateway`
- Type: Web Service
- Dockerfile Path: `Dockerfile.gateway`
- Health Check Path: `/health`

### Auth

- Name: `focus360-auth-service`
- Type: Private Service o Web Service
- Dockerfile Path: `Dockerfile.auth_service`
- Health Check Path: `/health`

### Tenant

- Dockerfile Path: `Dockerfile.tenant_service`

### Focus

- Dockerfile Path: `Dockerfile.focus_service`

### Wellness

- Dockerfile Path: `Dockerfile.wellness_service`

### Passport

- Dockerfile Path: `Dockerfile.passport_service`

### Billing

- Dockerfile Path: `Dockerfile.billing_service`

### Compliance

- Dockerfile Path: `Dockerfile.compliance_service`

### Locker

- Dockerfile Path: `Dockerfile.locker_service`

### Registry

- Dockerfile Path: `Dockerfile.registry_service`

## Variabili Gateway

Usa gli URL effettivi creati da Render:

```text
AUTH_URL=https://focus360-auth-service.onrender.com
TENANT_URL=https://focus360-tenant-service.onrender.com
FOCUS_URL=https://focus360-focus-service.onrender.com
WELLNESS_URL=https://focus360-wellness-service.onrender.com
PASSPORT_URL=https://focus360-passport-service.onrender.com
BILLING_URL=https://focus360-billing-service.onrender.com
COMPLIANCE_URL=https://focus360-compliance-service.onrender.com
LOCKER_URL=https://focus360-locker-service.onrender.com
REGISTRY_URL=https://focus360-registry-service.onrender.com
```

## Variabili comuni

```text
SECRET_KEY=una_chiave_lunga_sicura
INTERNAL_API_KEY=una_chiave_interna_lunga
DATABASE_URL=sqlite:////data/focus360_micro.db
PYTHONUNBUFFERED=1
```

Per produzione reale sostituire SQLite con PostgreSQL Render.

## Test

Gateway:

```text
https://focus360-gateway.onrender.com/health
https://focus360-gateway.onrender.com/health/services
```

Singolo servizio:

```text
https://focus360-auth-service.onrender.com/health
```

