# Fix Render: ModuleNotFoundError: No module named 'psycopg2'

Il problema era causato dall'assenza del driver PostgreSQL nei `requirements.txt` dei microservizi.

## Correzione applicata

È stata aggiunta la dipendenza:

```txt
psycopg2-binary==2.9.9
```

in:

- `requirements.txt` root
- `gateway/requirements.txt`
- `services/*/requirements.txt`
- `legacy_alpha_monolith/requirements.txt`

## Cosa fare su Render

Per ogni servizio già creato:

1. caricare questo nuovo ZIP/repository aggiornato su GitHub;
2. aprire il servizio Render;
3. eseguire `Manual Deploy`;
4. scegliere `Clear build cache & deploy`.

Se il servizio usa Docker, Render installerà automaticamente le dipendenze del `requirements.txt` presente nella Root Directory del servizio.

## Nota

Usare `psycopg2-binary` in questa fase prototipale evita errori di compilazione C su Render. In produzione enterprise si può valutare `psycopg` v3 o un'immagine Docker con librerie PostgreSQL native.
