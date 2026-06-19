# Deploy Focus360 AI con Frontend-Service + Gateway

## Obiettivo
Aggiungere al gateway microservizi una webapp grafica vendibile, basata sul monolite Alpha, con layout Bootstrap professionale.

## Locale Docker Compose
```powershell
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose ps
```

Aprire:
- Gateway: http://localhost:8080
- Webapp grafica: http://localhost:8090
- Health microservizi: http://localhost:8080/health/services
- Verifica collegamento frontend-gateway: http://localhost:8090/system-status

## Render
Creare un servizio aggiuntivo.

### Frontend Service
- Type: Web Service
- Environment: Docker
- Root Directory: `frontend-service`
- Dockerfile Path: `Dockerfile`

Variabili:
```env
SECRET_KEY=valore_sicuro
DATABASE_URL=sqlite:///focus360_ai.db
GATEWAY_URL=https://focus360-gateway.onrender.com
FRONTEND_MODE=frontend-service
```

### Gateway
Aggiungere:
```env
FRONTEND_URL=https://focus360-frontend-service.onrender.com
FRONTEND_PUBLIC_URL=https://focus360-frontend-service.onrender.com
```

Il Gateway espone:
- `/app` redirect alla webapp grafica
- `/frontend/health` verifica connessione frontend-service
