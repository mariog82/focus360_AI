# Focus360 AI - Render Standalone Path Fix

Questo pacchetto corregge gli errori:

- `/gateway: not found`
- `/services/auth_service: not found`

## Impostazione corretta su Render

Per ogni servizio usa **Root Directory = cartella del servizio** e **Dockerfile Path = Dockerfile**.

### Gateway pubblico
- New Web Service
- Environment: Docker
- Root Directory: `gateway`
- Dockerfile Path: `Dockerfile`
- Health Check Path: `/health`

### Auth Service
- New Web Service o Private Service
- Environment: Docker
- Root Directory: `services/auth_service`
- Dockerfile Path: `Dockerfile`
- Health Check Path: `/health`

### Tenant Service
- Root Directory: `services/tenant_service`

### Focus Service
- Root Directory: `services/focus_service`

### Wellness Service
- Root Directory: `services/wellness_service`

### Passport Service
- Root Directory: `services/passport_service`

### Billing Service
- Root Directory: `services/billing_service`

### Compliance Service
- Root Directory: `services/compliance_service`

### Locker Service
- Root Directory: `services/locker_service`

### Registry Service
- Root Directory: `services/registry_service`

## Variabili del Gateway

Nel Gateway inserisci gli URL pubblici/privati generati da Render:

AUTH_URL=https://focus360-auth-service.onrender.com
TENANT_URL=https://focus360-tenant-service.onrender.com
FOCUS_URL=https://focus360-focus-service.onrender.com
WELLNESS_URL=https://focus360-wellness-service.onrender.com
PASSPORT_URL=https://focus360-passport-service.onrender.com
BILLING_URL=https://focus360-billing-service.onrender.com
COMPLIANCE_URL=https://focus360-compliance-service.onrender.com
LOCKER_URL=https://focus360-locker-service.onrender.com
REGISTRY_URL=https://focus360-registry-service.onrender.com

## Perché funziona

Ogni microservizio ora contiene:
- il proprio `Dockerfile`;
- il proprio `requirements.txt`;
- una copia della cartella `shared` necessaria agli import Python;
- un comando `gunicorn app:app` coerente con la Root Directory scelta.

In questo modo Render non deve più cercare cartelle fuori dal contesto di build.
