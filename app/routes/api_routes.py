import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from app.config import Config
from app.services.payment_service import ClickHandler, PaymeHandler

api_bp = Blueprint('api', __name__)

@api_bp.route('/click/prepare', methods=['POST'])
def click_prepare():
    """Click Prepare Webhook"""
    data = request.form.to_dict()
    response = ClickHandler.handle_request(data)
    return jsonify(response)


@api_bp.route('/click/complete', methods=['POST'])
def click_complete():
    """Click Complete Webhook"""
    data = request.form.to_dict()
    response = ClickHandler.handle_request(data)
    return jsonify(response)


@api_bp.route('/payme', methods=['POST'])
def payme_webhook():
    """Payme JSON-RPC Webhook"""
    auth_header = request.headers.get('Authorization', '')
    body_json = request.get_json(force=True, silent=True) or {}
    response = PaymeHandler.handle_rpc(auth_header, body_json)
    return jsonify(response)


@api_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Yuklangan fayllarni xavfsiz taqdim etish"""
    return send_from_directory(Config.UPLOAD_FOLDER, filename)
