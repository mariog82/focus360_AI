# Focus360 AI - Render Root Safe Deploy

Questa versione ha struttura piatta: appena apri il repository vedi direttamente `gateway/` e `services/`.

## Configurazione Render corretta

### Gateway
- Root Directory: `gateway`
- Dockerfile Path: `Dockerfile`

### Auth
- Root Directory: `services/auth_service`
- Dockerfile Path: `Dockerfile`

### Tenant
- Root Directory: `services/tenant_service`
- Dockerfile Path: `Dockerfile`

### Focus
- Root Directory: `services/focus_service`
- Dockerfile Path: `Dockerfile`

### Wellness
- Root Directory: `services/wellness_service`
- Dockerfile Path: `Dockerfile`

### Passport
- Root Directory: `services/passport_service`
- Dockerfile Path: `Dockerfile`

### Billing
- Root Directory: `services/billing_service`
- Dockerfile Path: `Dockerfile`

### Compliance
- Root Directory: `services/compliance_service`
- Dockerfile Path: `Dockerfile`

### Locker
- Root Directory: `services/locker_service`
- Dockerfile Path: `Dockerfile`

### Registry
- Root Directory: `services/registry_service`
- Dockerfile Path: `Dockerfile`

## Errore tipico
Se Render cerca `/services/auth_service` e dice `not found`, significa che nel repository non hai caricato il contenuto della cartella principale, ma una cartella contenitore. In GitHub devi vedere subito:

```
gateway/
services/
docker-compose.yml
render.yaml
```

non:

```
focus360_render_standalone_fix/gateway/
focus360_render_standalone_fix/services/
```
