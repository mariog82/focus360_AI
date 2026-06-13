# Focus360 AI

Piattaforma web multi-istituto per benessere digitale, concentrazione a lezione, gamification, report scolastici e certificazione educativa.

## Novità della versione rigenerata

- **Digital Wellness Score™**: indicatore 0-100 per studente, classe e istituto.
- **Focus360 AI Educational Passport™**: portfolio digitale verificabile dello studente.
- Registro Focus con QR temporaneo docente.
- Gamification: punti Focus, FocusToken e badge.
- Blockchain educativa prototipo: hash per sessioni, badge e certificazioni.
- Dashboard SuperAdmin, Dirigente, Docente, Studente e Genitore.
- Upload CSV docenti/studenti.
- Report CSV e report ministeriale.
- Smart locker / phone box, consensi genitori, piani di intervento, API device-event.

## Digital Wellness Score™

Formula trasparente:

```python
score = (
  focus_continuity * 0.30 +
  digital_discipline * 0.25 +
  consistency * 0.15 +
  collaborative_focus * 0.15 +
  digital_citizenship * 0.15
)
```

Livelli:

- 0-39 Critico
- 40-59 Da migliorare
- 60-79 Buono
- 80-100 Eccellente

## Educational Passport™

Il passaporto raccoglie:

- ore Focus;
- FocusToken;
- badge;
- Educazione Civica;
- PCTO;
- AI Literacy;
- Cybersecurity;
- Soft Skills;
- hash di verifica su ledger educativo.

## Avvio locale

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
flask --app app init-db
python app.py
```

Apri: http://127.0.0.1:5000

Credenziali demo:

```text
superadmin@focus360.ai
admin123
```

## CSV docenti

Separatore `;`:

```text
cognome;nome;disciplina;mail;telefono;classe
Rossi;Mario;Informatica;mario.rossi@scuola.it;3330000000;4A
```

## CSV studenti

```text
cognome;nome;data di nascita;email;telefono;classe
Bianchi;Luca;2009-05-10;luca.bianchi@scuola.it;3331111111;4A
```

## Deploy su Render

1. Crea un repository GitHub e carica tutti i file.
2. Su Render scegli **New + → Web Service**.
3. Collega il repository.
4. Imposta:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Variabili d'ambiente:

```text
SECRET_KEY=una_chiave_lunga_sicura
DATABASE_URL=sqlite:///focus360_ai.db
```

Per produzione commerciale usare PostgreSQL Render:

```text
DATABASE_URL=<Internal Database URL del database PostgreSQL Render>
```

## Note commerciali

Focus360 AI non deve essere presentata come app di controllo, ma come piattaforma per:

- benessere digitale;
- cittadinanza digitale;
- report PTOF/educazione civica;
- PCTO e portfolio competenze;
- riduzione della distrazione digitale;
- dialogo scuola-famiglia.


## Fix deploy Render - pandas rimosso
Questa versione non richiede pandas. L'esportazione CSV usa solo la libreria standard Python (`csv` + `io`) per evitare errori di compilazione su Render come `metadata-generation-failed` o `ninja: build stopped`.

Se Render continua a usare una cache vecchia, fare:
1. Render Dashboard -> Web Service -> Manual Deploy.
2. Selezionare **Clear build cache & deploy**.
3. Verificare che `requirements.txt` non contenga `pandas`, `numpy` o `scikit-learn` nella versione prototipo.


## Focus360 AI Enterprise - ambiente demo

Dopo il login come SuperAdmin puoi usare il pulsante **Genera scuola demo** nella console aziendale.

Credenziali demo generate:

| Ruolo | Email | Password |
|---|---|---|
| SuperAdmin | superadmin@focus360.ai | admin123 |
| Dirigente Demo | dirigente@demo.focus360.ai | dirigente123 |
| Docente Demo | docente@demo.focus360.ai | docente123 |
| Studente Demo | studente@demo.focus360.ai | studente123 |
| Genitore Demo | genitore@demo.focus360.ai | genitore123 |

Il pulsante crea automaticamente un tenant Enterprise con classi, docenti, studenti, genitori, lezioni, record focus, Digital Wellness Score, Educational Passport, badge NFT educativi, consensi, smart locker, pagamento demo e report ministeriali.

Per Render è incluso `runtime.txt` con Python 3.11.9 per evitare problemi di compilazione delle dipendenze native.
