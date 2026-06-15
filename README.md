# Focus360 AI Enterprise v11 – v9 base + multi-plesso

Questa versione riparte da `focus360_ai_enterprise_v9_real_plan_modules.zip` e applica le modifiche richieste:

## Modifiche principali

- Moduli **lockers**, **api** e **registro** disattivati lato piano e lato server.
- Il piano Enterprise/PNRR mantiene: QR, dashboard, CSV, gamification, AI, Wellness Score, Passport, interventi, report famiglie, blockchain badge, report ministeriali, **multi_plesso** e supporto prioritario.
- Aggiunta funzione **Multi-plesso** solo per Enterprise/PNRR.
- Aggiunta tabella `Plesso` con sedi/succursali.
- Aggiunte route:
  - `/plessi`
  - `/plessi/<id>/edit`
  - `/plessi/<id>/delete`
- Aggiunto menu “Multi-plesso” per Dirigente Enterprise/PNRR e SuperAdmin.
- La Demo viene mantenuta e arricchita con due plessi:
  - Sede centrale
  - Succursale Tecnologica

## Moduli disattivati

In questa build i seguenti moduli non sono utilizzabili anche se presenti nel codice storico:

- `lockers`
- `api`
- `registro`

Sono rimasti nel progetto come predisposizione futura, ma `plan_enabled()` restituisce sempre `False`.

## Credenziali demo

- SuperAdmin: `superadmin@focus360.ai` / `admin123`
- Dirigente: `dirigente@demo.focus360.ai` / `dirigente123`
- Docente: `docente@demo.focus360.ai` / `docente123`
- Studente: `studente@demo.focus360.ai` / `studente123`
- Genitore: `genitore@demo.focus360.ai` / `genitore123`

## Deploy Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

Variabili consigliate:

```env
SECRET_KEY=una_chiave_lunga_sicura
DATABASE_URL=sqlite:///focus360_ai.db
```

Per produzione reale usare PostgreSQL Render.
