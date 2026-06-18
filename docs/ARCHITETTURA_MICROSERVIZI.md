
# Focus360 AI Alpha - Architettura SaaS a microservizi

## Servizi
- **API Gateway**: unico punto d'ingresso, routing verso i servizi.
- **Auth Service**: login, ruoli, credenziali temporanee, cambio password.
- **Tenant Service**: istituzioni scolastiche, piani, stato licenza, multi-tenant.
- **Focus Service**: lezioni, QR, partecipazione studente, timer, completamento focus.
- **Wellness Service**: Digital Wellness Score e KPI.
- **Passport Service**: Educational Passport, elementi portfolio, export.
- **Locker Service**: eventi Smart Locker/Phone Box, protetti da API key interna.
- **Registry Service**: prototipo integrazione registro elettronico.
- **Billing Service**: scadenze licenza e notifiche.
- **Compliance Service**: checklist GDPR/CAD/AGID/NIS2/DevSecOps.

## Pattern SaaS
Il tenant è l'istituzione scolastica. Ogni dato operativo deve essere filtrato per `tenant_id`. In produzione si consiglia PostgreSQL con schema condiviso + row-level security oppure database per tenant negli istituti più grandi.
