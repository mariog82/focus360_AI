
from flask import request, jsonify
from shared.app_factory import create_service_app
app=create_service_app('registry-service')
@app.post('/registro/import')
def import_registry():
    data=request.json or {}; return jsonify({'status':'prototype_import_received','source':data.get('source','registro_elettronico'),'records':len(data.get('records',[]))})
@app.get('/registro/capabilities')
def caps(): return jsonify({'supported':['students','teachers','classes','attendance_export'],'mode':'prototype'})
