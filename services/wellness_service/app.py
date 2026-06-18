
from flask import request, jsonify
from shared.app_factory import create_service_app
from shared.models import db, WellnessScore
app=create_service_app('wellness-service')
def calc(d): return int(d.get('focus_continuity',70)*.30+d.get('digital_discipline',70)*.25+d.get('consistency',70)*.15+d.get('collaborative_focus',70)*.15+d.get('digital_citizenship',70)*.15)
@app.post('/wellness/recalculate/<int:user_id>')
def recalc(user_id):
    d=request.json or {}; score=calc(d); w=WellnessScore.query.filter_by(user_id=user_id).first() or WellnessScore(user_id=user_id)
    for k in ['focus_continuity','digital_discipline','consistency','collaborative_focus','digital_citizenship']:
        if k in d: setattr(w,k,int(d[k]))
    w.score=score; db.session.add(w); db.session.commit(); return jsonify({'user_id':user_id,'score':score})
@app.get('/wellness/<int:user_id>')
def get_score(user_id):
    w=WellnessScore.query.filter_by(user_id=user_id).first(); return jsonify({'score': w.score if w else 70})
