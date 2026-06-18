from flask import Flask, jsonify, request, Response, redirect
import os
import requests

app = Flask(__name__)

SERVICES = {
    'auth': os.getenv('AUTH_URL', 'http://auth-service:8000'),
    'tenant': os.getenv('TENANT_URL', 'http://tenant-service:8000'),
    'focus': os.getenv('FOCUS_URL', 'http://focus-service:8000'),
    'wellness': os.getenv('WELLNESS_URL', 'http://wellness-service:8000'),
    'passport': os.getenv('PASSPORT_URL', 'http://passport-service:8000'),
    'locker': os.getenv('LOCKER_URL', 'http://locker-service:8000'),
    'registry': os.getenv('REGISTRY_URL', 'http://registry-service:8000'),
    'billing': os.getenv('BILLING_URL', 'http://billing-service:8000'),
    'compliance': os.getenv('COMPLIANCE_URL', 'http://compliance-service:8000'),
}


def _html_page(title: str, body: str, status: int = 200) -> Response:
    html = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ background:#f4f7fb; }}
    .hero {{ border-radius:24px; background:linear-gradient(135deg,#0d47a1,#1976d2); color:white; }}
    .badge-soft {{ background:#e3f2fd; color:#0d47a1; }}
    code {{ color:#0d47a1; }}
  </style>
</head>
<body>
  <main class="container py-5">
    {body}
  </main>
</body>
</html>"""
    return Response(html, status=status, mimetype="text/html")


@app.get('/')
def index():
    service_cards = ''.join(
        f'<li class="list-group-item d-flex justify-content-between align-items-center">'
        f'<span><strong>{name}</strong><br><small class="text-muted">{url}</small></span>'
        f'<span class="badge badge-soft rounded-pill">/api/{name}/...</span></li>'
        for name, url in SERVICES.items()
    )
    body = f"""
    <section class="hero p-5 mb-4 shadow-sm">
      <h1 class="display-5 fw-bold">Focus360 AI Alpha</h1>
      <p class="lead mb-0">API Gateway SaaS a microservizi attivo su Render.</p>
    </section>
    <div class="row g-4">
      <div class="col-lg-7">
        <div class="card shadow-sm border-0">
          <div class="card-body p-4">
            <h2 class="h4">Deploy avviato correttamente</h2>
            <p>Questa versione microservizi espone un <strong>API Gateway</strong>. Non è la dashboard monolitica grafica: le UI complete sono nella cartella <code>legacy_alpha_monolith</code> oppure nei singoli frontend da collegare ai servizi.</p>
            <div class="d-flex gap-2 flex-wrap">
              <a class="btn btn-primary" href="/health">Verifica health</a>
              <a class="btn btn-outline-primary" href="/docs">Documentazione deploy</a>
            </div>
          </div>
        </div>
        <div class="card shadow-sm border-0 mt-4">
          <div class="card-body p-4">
            <h2 class="h4">Endpoint principali</h2>
            <ul>
              <li><code>/health</code> stato gateway e configurazione servizi.</li><li><code>/health/services</code> verifica reale di connessione ai microservizi.</li>
              <li><code>/api/&lt;service&gt;/&lt;path&gt;</code> proxy verso i microservizi.</li>
              <li><code>/docs</code> istruzioni operative per Render e microservizi.</li>
            </ul>
          </div>
        </div>
      </div>
      <div class="col-lg-5">
        <div class="card shadow-sm border-0">
          <div class="card-body p-4">
            <h2 class="h5">Servizi configurati</h2>
            <ul class="list-group list-group-flush">{service_cards}</ul>
          </div>
        </div>
      </div>
    </div>
    """
    return _html_page("Focus360 AI Alpha", body)


@app.get('/docs')
def docs():
    body = """
    <section class="card shadow-sm border-0">
      <div class="card-body p-4">
        <h1 class="h3">Focus360 AI Alpha - note di deploy</h1>
        <p>Se su Render appareva <em>Not Found</em>, il motivo era che l'API Gateway non aveva una route <code>/</code>. Ora la homepage è presente.</p>
        <h2 class="h5 mt-4">Modalità 1 - deploy gateway singolo su Render</h2>
        <pre class="bg-light p-3 rounded">Build Command: pip install --upgrade pip && pip install -r requirements.txt
Start Command: gunicorn app:app --bind 0.0.0.0:$PORT</pre>
        <p>Questa modalità avvia il gateway, utile per demo tecnica/API.</p>
        <h2 class="h5 mt-4">Modalità 2 - webapp grafica completa</h2>
        <p>Per usare la UI monolitica completa, entra nella cartella <code>legacy_alpha_monolith</code> e fai deploy di quella app con <code>gunicorn app:app</code>.</p>
        <h2 class="h5 mt-4">Modalità 3 - microservizi completi</h2>
        <p>Usa <code>docker-compose.yml</code> in ambiente Docker/Kubernetes oppure crea un servizio Render separato per ogni microservizio e imposta le variabili <code>AUTH_URL</code>, <code>TENANT_URL</code>, ecc.</p>
        <a class="btn btn-primary mt-3" href="/">Torna alla home</a>
      </div>
    </section>
    """
    return _html_page("Focus360 AI Docs", body)


@app.get('/health')
def health():
    return jsonify({'gateway': 'ok', 'mode': 'alpha-microservices-render', 'services': SERVICES})




@app.get('/health/services')
def health_services():
    """Verifica raggiungibilità reale dei microservizi dalla rete Docker interna."""
    results = {}
    overall = 'ok'
    for name, base_url in SERVICES.items():
        target = f"{base_url.rstrip('/')}/health"
        try:
            r = requests.get(target, timeout=3, headers={'X-Internal-API-Key': os.getenv('INTERNAL_API_KEY', 'dev-internal-key-change-me')})
            results[name] = {
                'url': target,
                'status_code': r.status_code,
                'reachable': r.status_code == 200,
                'body': r.json() if r.headers.get('content-type','').startswith('application/json') else r.text[:200]
            }
            if r.status_code != 200:
                overall = 'degraded'
        except requests.RequestException as exc:
            results[name] = {'url': target, 'reachable': False, 'error': str(exc)}
            overall = 'degraded'
    return jsonify({'gateway': 'ok', 'overall': overall, 'services': results}), (200 if overall == 'ok' else 503)


@app.route('/api/<service>/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def proxy(service, path):
    if service not in SERVICES:
        return jsonify({'error': 'unknown service', 'available_services': list(SERVICES.keys())}), 404
    url = f"{SERVICES[service].rstrip('/')}/{path}"
    try:
        response = requests.request(
            request.method,
            url,
            json=request.get_json(silent=True),
            params=request.args,
            headers={'X-Internal-API-Key': os.getenv('INTERNAL_API_KEY', 'dev-internal-key-change-me')},
            timeout=10,
        )
        excluded_headers = {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}
        headers = [(k, v) for k, v in response.headers.items() if k.lower() not in excluded_headers]
        return (response.content, response.status_code, headers)
    except requests.RequestException as exc:
        return jsonify({'error': 'service_unreachable', 'service': service, 'url': url, 'detail': str(exc)}), 502


@app.errorhandler(404)
def not_found(_error):
    body = """
    <section class="card shadow-sm border-0">
      <div class="card-body p-4">
        <h1 class="h3 text-danger">Pagina non trovata</h1>
        <p>L'URL richiesto non corrisponde a una route del gateway.</p>
        <p>Usa la home <code>/</code>, lo stato <code>/health</code> oppure un endpoint <code>/api/&lt;service&gt;/&lt;path&gt;</code>.</p>
        <a class="btn btn-primary" href="/">Vai alla home</a>
      </div>
    </section>
    """
    return _html_page("Not Found - Focus360 AI", body, status=404)
