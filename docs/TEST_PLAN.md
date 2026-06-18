
# Piano di test

## Test di integrazione
Verificano healthcheck servizi, validazione campi obbligatori e contratti API.

## Test di sistema
Verificano il flusso QR: docente avvia sessione, studente entra, completamento focus, punti/token.

## Test di accettazione
Scenario scuola: SuperAdmin crea istituto, crea utente, verifica credenziali temporanee.

## Test di sicurezza
Verificano endpoint interni protetti, password non salvate in chiaro, SAST e dependency checking.

## Esecuzione
```bash
pip install -r requirements.txt
./scripts/run_tests.sh
./scripts/devsecops_scan.sh
```
