# Fix PostgreSQL driver Render/Docker

Errore risolto:

```
ModuleNotFoundError: No module named 'psycopg2'
```

Causa: `DATABASE_URL` punta a PostgreSQL e SQLAlchemy usa il dialetto `postgresql://`, che richiede il driver `psycopg2`.

Correzione applicata:

```txt
psycopg2-binary==2.9.9
```

Dopo aver caricato questa versione su GitHub/Render:

1. eseguire redeploy del servizio;
2. se Render usa cache vecchia, scegliere **Clear build cache & deploy**;
3. verificare `/health`.
