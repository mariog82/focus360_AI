# Focus360 AI Enterprise v10 - Moduli visibili solo se attivi

Questa versione corregge la visualizzazione dei moduli per piano e per utente.

## Modifica principale
Nelle dashboard e nella pagina `/modules` vengono mostrati solo i moduli realmente utilizzabili dall'istituto, cioè quelli inclusi nel piano acquistato e non disattivati dal SuperAdmin.

I moduli non attivi:
- non compaiono più come label/grigi/disabilitati;
- non appaiono più nelle dashboard di Dirigente, Docente, Studente e Genitore;
- restano comunque bloccati lato server tramite `require_feature()`.

## Logica piani
- Base: QR, dashboard, CSV, report CSV, gamification base.
- Pro: Base + AI, Wellness Score, Educational Passport, ranking, report famiglie, interventi.
- Enterprise/PNRR: Pro + Smart Locker, blockchain, API, registro, report ministeriale, multi-plesso.

## Avvio locale
```bash
pip install -r requirements.txt
python app.py
```

Credenziali demo:
- `superadmin@focus360.ai` / `admin123`
