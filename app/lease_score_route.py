
from flask import request, jsonify
from flask_jwt_extended import jwt_required

@app.route('/api/ai/lease-score', methods=['POST'])
@jwt_required()
def lease_score():
    data = request.get_json()
    income = data.get('income', 0)
    credit_score = data.get('credit_score', 0)
    history = data.get('history', '')

    score = min(max((int(credit_score) / 850) * 60 + (int(income) / 100000) * 30, 0), 100)
    if "eviction" in history.lower():
        score -= 20

    if score >= 75:
        risk = "low"
    elif score >= 50:
        risk = "medium"
    else:
        risk = "high"

    return jsonify({"score": round(score, 1), "risk": risk})
