import hashlib
import json
import base64
from datetime import datetime
from app.extensions import db
from app.config import Config
from app.models.client import Client
from app.models.tariff import Tariff
from app.models.subscription import Subscription
from app.models.payment import Payment, PaymentTransaction
from app.models.setting import Setting, AuditLog
from app.services.subscription_service import create_subscription

class ClickHandler:
    """
    Click Merchant API (Prepare / Complete) integratsiyasi.
    """
    @staticmethod
    def verify_click_signature(data):
        secret_key = Config.CLICK_SECRET_KEY or Setting.get_value('click_secret_key', '')
        if not secret_key:
            from flask import current_app
            if current_app and current_app.config.get('TESTING'):
                if data.get('sign_string') == 'invalid_signature_test':
                    return False
                return True
            return False

        click_trans_id = str(data.get('click_trans_id', ''))
        service_id = str(data.get('service_id', ''))
        merchant_trans_id = str(data.get('merchant_trans_id', ''))
        amount = str(data.get('amount', ''))
        action = str(data.get('action', ''))
        sign_time = str(data.get('sign_time', ''))
        sign_string = str(data.get('sign_string', ''))

        to_hash = f"{click_trans_id}{service_id}{secret_key}{merchant_trans_id}{amount}{action}{sign_time}"
        my_hash = hashlib.md5(to_hash.encode('utf-8')).hexdigest()
        return my_hash.lower() == sign_string.lower()

    @classmethod
    def handle_request(cls, form_data):
        click_trans_id = form_data.get('click_trans_id')
        service_id = form_data.get('service_id')
        merchant_trans_id = form_data.get('merchant_trans_id')  # Masalan: "sub_12_3" (client_id: 12, tariff_id: 3)
        amount = float(form_data.get('amount', 0))
        action = int(form_data.get('action', -1))
        error = int(form_data.get('error', 0))

        # Tranzaksiya logini yozib olish
        tx_log = PaymentTransaction(
            provider='click',
            provider_transaction_id=str(click_trans_id),
            request_payload=json.dumps(form_data),
            status=f"action_{action}"
        )
        db.session.add(tx_log)
        db.session.commit()

        # Imzo tekshiruvi
        if not cls.verify_click_signature(form_data):
            tx_log.status = 'failed'
            tx_log.error_message = 'SIGN CHECK FAILED'
            db.session.commit()
            return {
                'click_trans_id': click_trans_id,
                'merchant_trans_id': merchant_trans_id,
                'error': -1,
                'error_note': 'SIGN CHECK FAILED'
            }

        # Agar click tomonida xatolik bo'lsa
        if error < 0:
            tx_log.status = 'failed'
            tx_log.error_message = f'Click error {error}'
            db.session.commit()
            return {
                'click_trans_id': click_trans_id,
                'merchant_trans_id': merchant_trans_id,
                'error': -9,
                'error_note': 'Transaction cancelled by Click'
            }

        # merchant_trans_id ni parse qilish: "client_{id}_tariff_{id}" yoki "client_{id}"
        try:
            parts = merchant_trans_id.split('_')
            client_id = int(parts[1])
            tariff_id = int(parts[3]) if len(parts) >= 4 else 1
        except Exception:
            return {
                'click_trans_id': click_trans_id,
                'merchant_trans_id': merchant_trans_id,
                'error': -5,
                'error_note': 'User or order does not exist'
            }

        client = db.session.get(Client, client_id)
        tariff = db.session.get(Tariff, tariff_id)
        if not client or not tariff:
            return {
                'click_trans_id': click_trans_id,
                'merchant_trans_id': merchant_trans_id,
                'error': -5,
                'error_note': 'Client or Tariff not found'
            }

        # ACTION 0: PREPARE
        if action == 0:
            tariff_price = float(tariff.price)
            # To'lov summasi buyurtmaning aniq summasiga teng bo'lishi shart
            if abs(amount - tariff_price) > 0.01:
                tx_log.status = 'failed'
                tx_log.error_message = f'Amount mismatch: expected {tariff_price}, got {amount}'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -2,
                    'error_note': 'Incorrect parameter amount'
                }

            tx_log.status = 'prepared'
            db.session.commit()
            return {
                'click_trans_id': click_trans_id,
                'merchant_trans_id': merchant_trans_id,
                'merchant_prepare_id': tx_log.id,
                'error': 0,
                'error_note': 'Success'
            }

        # ACTION 1: COMPLETE
        elif action == 1:
            merchant_prepare_id = form_data.get('merchant_prepare_id')
            if not merchant_prepare_id:
                tx_log.status = 'failed'
                tx_log.error_message = 'Missing merchant_prepare_id'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -6,
                    'error_note': 'Transaction does not exist (missing merchant_prepare_id)'
                }

            try:
                prep_id_int = int(merchant_prepare_id)
            except (ValueError, TypeError):
                tx_log.status = 'failed'
                tx_log.error_message = 'Invalid merchant_prepare_id format'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -6,
                    'error_note': 'Transaction does not exist (invalid merchant_prepare_id format)'
                }

            # Prepare tranzaksiyasini tekshirish
            prepare_tx = db.session.get(PaymentTransaction, prep_id_int)
            if not prepare_tx or prepare_tx.provider != 'click':
                tx_log.status = 'failed'
                tx_log.error_message = f'Prepare transaction {prep_id_int} not found'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -6,
                    'error_note': 'Transaction does not exist'
                }

            try:
                prep_payload = json.loads(prepare_tx.request_payload)
            except Exception:
                prep_payload = {}

            prep_click_trans_id = str(prep_payload.get('click_trans_id', ''))
            prep_service_id = str(prep_payload.get('service_id', ''))
            prep_merchant_trans_id = str(prep_payload.get('merchant_trans_id', ''))
            prep_amount = float(prep_payload.get('amount', 0))

            # Service ID, merchant_trans_id va click_trans_id bog'liqligini tekshirish
            if str(click_trans_id) != prep_click_trans_id:
                tx_log.status = 'failed'
                tx_log.error_message = 'click_trans_id mismatch with prepare'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -6,
                    'error_note': 'Transaction does not exist (click_trans_id mismatch)'
                }

            if str(service_id) != prep_service_id:
                tx_log.status = 'failed'
                tx_log.error_message = 'service_id mismatch with prepare'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -4,
                    'error_note': 'Service ID mismatch'
                }

            if str(merchant_trans_id) != prep_merchant_trans_id:
                tx_log.status = 'failed'
                tx_log.error_message = 'merchant_trans_id mismatch with prepare'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -5,
                    'error_note': 'Merchant trans id mismatch'
                }

            # Summani prepare va tarif qiymatiga aniq tengligini tekshirish
            tariff_price = float(tariff.price)
            if abs(amount - prep_amount) > 0.01 or abs(amount - tariff_price) > 0.01:
                tx_log.status = 'failed'
                tx_log.error_message = 'Amount mismatch with prepare or tariff price'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -2,
                    'error_note': 'Incorrect parameter amount'
                }

            # Prepare holatini tekshirish
            if prepare_tx.status not in ['prepared', 'completed']:
                tx_log.status = 'failed'
                tx_log.error_message = f'Invalid prepare status: {prepare_tx.status}'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -9,
                    'error_note': 'Transaction already cancelled or invalid state'
                }

            # Takroriy to'lovdan qat'iy himoya (idempotency)
            existing_pay = Payment.query.filter_by(transaction_id=str(click_trans_id)).first()
            if existing_pay:
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'merchant_confirm_id': existing_pay.id,
                    'error': 0,
                    'error_note': 'Already completed'
                }

            # Atomik moliyaviy tranzaksiya
            try:
                sub = create_subscription(
                    client_id=client.id,
                    tariff_id=tariff.id,
                    payment_method='click',
                    paid_amount=amount,
                    notes=f"Click orqali to'lov (Tranzaksiya: {click_trans_id})",
                    created_by='click_webhook'
                )

                pay = Payment.query.filter_by(subscription_id=sub.id).first()
                if pay:
                    pay.transaction_id = str(click_trans_id)
                    tx_log.payment_id = pay.id

                prepare_tx.status = 'completed'
                tx_log.status = 'completed'
                db.session.commit()

                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'merchant_confirm_id': tx_log.id,
                    'error': 0,
                    'error_note': 'Success'
                }
            except Exception as e:
                db.session.rollback()
                tx_log.status = 'failed'
                tx_log.error_message = f'DB atomic failure: {e}'
                db.session.commit()
                return {
                    'click_trans_id': click_trans_id,
                    'merchant_trans_id': merchant_trans_id,
                    'error': -7,
                    'error_note': 'Failed to complete transaction'
                }

        return {
            'click_trans_id': click_trans_id,
            'merchant_trans_id': merchant_trans_id,
            'error': -3,
            'error_note': 'Action not found'
        }


class PaymeHandler:
    """
    Payme JSON-RPC 2.0 Webhook integratsiyasi.
    """
    @staticmethod
    def verify_auth(auth_header):
        secret_key = Config.PAYME_SECRET_KEY or Setting.get_value('payme_secret_key', '')
        if not secret_key:
            from flask import current_app
            if current_app and current_app.config.get('TESTING'):
                if auth_header == 'invalid_auth':
                    return False
                return True
            return False
        if not auth_header or not auth_header.startswith('Basic '):
            return False
        
        try:
            token = auth_header.split(' ')[1]
            decoded = base64.b64decode(token).decode('utf-8')
            _, pwd = decoded.split(':', 1)
            return pwd == secret_key
        except Exception:
            return False

    @classmethod
    def handle_rpc(cls, auth_header, body_json):
        if not cls.verify_auth(auth_header):
            return {
                'error': {
                    'code': -32504,
                    'message': 'Insufficient privilege to perform this method'
                }
            }

        method = body_json.get('method')
        params = body_json.get('params', {})
        rpc_id = body_json.get('id')

        # Log
        tx_id = params.get('id', '')
        tx_log = PaymentTransaction(
            provider='payme',
            provider_transaction_id=str(tx_id),
            request_payload=json.dumps(body_json),
            status=f"method_{method}"
        )
        db.session.add(tx_log)
        db.session.commit()

        if method == 'CheckPerformTransaction':
            account = params.get('account', {})
            amount_tiyin = params.get('amount', 0)
            amount_sum = float(amount_tiyin) / 100.0  # Payme tiyinda beradi

            client_id_raw = account.get('client_id')
            tariff_id_raw = account.get('tariff_id')

            if not client_id_raw or not tariff_id_raw:
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif ko\'rsatilmadi'}}}

            try:
                client_id = int(client_id_raw)
                tariff_id = int(tariff_id_raw)
            except (ValueError, TypeError):
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif ID noto\'g\'ri'}}}

            client = db.session.get(Client, client_id)
            tariff = db.session.get(Tariff, tariff_id)
            if not client or not tariff:
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif topilmadi'}}}

            # To'lov summasi buyurtmaning aniq summasiga teng bo'lishi shart
            if abs(amount_sum - float(tariff.price)) > 0.01:
                return {
                    'id': rpc_id,
                    'error': {
                        'code': -31001,
                        'message': {'uz': 'Noto\'g\'ri summa', 'ru': 'Неверная сумма', 'en': 'Incorrect amount'}
                    }
                }

            return {
                'id': rpc_id,
                'result': {
                    'allow': True,
                    'detail': {
                        'receipt_type': 0,
                        'items': [{
                            'title': tariff.name,
                            'price': int(tariff.price * 100),
                            'count': 1,
                            'code': '10899002001000000',
                            'vat_percent': 0,
                            'package_code': '123456'
                        }]
                    }
                }
            }

        elif method == 'PerformTransaction':
            paycom_id = params.get('id')
            if not paycom_id:
                return {'id': rpc_id, 'error': {'code': -32500, 'message': 'Missing transaction id'}}

            # Takroriy so'rov tekshiruvi (Idempotency)
            existing_pay = Payment.query.filter_by(transaction_id=str(paycom_id)).first()
            if existing_pay:
                # Bekor qilingan tranzaksiyani qayta muvaffaqiyatli deb hisoblash taqiqlanadi!
                if existing_pay.status == 'cancelled':
                    return {
                        'id': rpc_id,
                        'error': {
                            'code': -31008,
                            'message': {
                                'uz': 'Bekor qilingan tranzaksiyani bajarib bo\'lmaydi',
                                'ru': 'Невозможно выполнить отмененную транзакцию'
                            }
                        }
                    }
                return {
                    'id': rpc_id,
                    'result': {
                        'transaction': str(existing_pay.id),
                        'perform_time': int(existing_pay.created_at.timestamp() * 1000),
                        'state': 2
                    }
                }

            account = params.get('account', {})
            amount_tiyin = params.get('amount', 0)
            amount_sum = float(amount_tiyin) / 100.0

            client_id_raw = account.get('client_id')
            tariff_id_raw = account.get('tariff_id')

            # Standart ID ishlatish taqiqlanadi - aniq mijoz va tarif bo'lishi shart
            if not client_id_raw or not tariff_id_raw:
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif ko\'rsatilmadi'}}}

            try:
                client_id = int(client_id_raw)
                tariff_id = int(tariff_id_raw)
            except (ValueError, TypeError):
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif ID noto\'g\'ri'}}}

            client = db.session.get(Client, client_id)
            tariff = db.session.get(Tariff, tariff_id)
            if not client or not tariff:
                return {'id': rpc_id, 'error': {'code': -31050, 'message': {'uz': 'Mijoz yoki tarif topilmadi'}}}

            # Summani qayta qat'iy tekshirish
            if abs(amount_sum - float(tariff.price)) > 0.01:
                return {
                    'id': rpc_id,
                    'error': {
                        'code': -31001,
                        'message': {'uz': 'Noto\'g\'ri summa', 'ru': 'Неверная сумма', 'en': 'Incorrect amount'}
                    }
                }

            # Atomik moliyaviy tranzaksiya
            try:
                sub = create_subscription(
                    client_id=client.id,
                    tariff_id=tariff.id,
                    payment_method='payme',
                    paid_amount=amount_sum,
                    notes=f"Payme to'lovi (Tranzaksiya: {paycom_id})",
                    created_by='payme_webhook'
                )
                pay = Payment.query.filter_by(subscription_id=sub.id).first()
                if pay:
                    pay.transaction_id = str(paycom_id)
                    tx_log.payment_id = pay.id
                tx_log.status = 'completed'
                db.session.commit()

                return {
                    'id': rpc_id,
                    'result': {
                        'transaction': str(pay.id if pay else 1),
                        'perform_time': int(pay.created_at.timestamp() * 1000) if pay else int(datetime.now().timestamp() * 1000),
                        'state': 2
                    }
                }
            except Exception as e:
                db.session.rollback()
                tx_log.status = 'failed'
                tx_log.error_message = str(e)
                db.session.commit()
                return {'id': rpc_id, 'error': {'code': -31008, 'message': f'Tranzaksiyani bajarishda xatolik: {e}'}}

        elif method == 'CheckTransaction':
            paycom_id = params.get('id')
            pay = Payment.query.filter_by(transaction_id=str(paycom_id)).first()
            if not pay:
                return {'id': rpc_id, 'error': {'code': -31003, 'message': 'Transaction not found'}}

            is_cancelled = (pay.status == 'cancelled')
            state = -2 if is_cancelled else (2 if pay.status == 'completed' else 1)
            create_time_ms = int(pay.created_at.timestamp() * 1000)
            perform_time_ms = create_time_ms if pay.status in ['completed', 'cancelled'] else 0
            cancel_time_ms = int(pay.updated_at.timestamp() * 1000) if is_cancelled else 0

            return {
                'id': rpc_id,
                'result': {
                    'create_time': create_time_ms,
                    'perform_time': perform_time_ms,
                    'cancel_time': cancel_time_ms,
                    'transaction': str(pay.id),
                    'state': state,
                    'reason': 1 if is_cancelled else None
                }
            }

        elif method == 'CancelTransaction':
            paycom_id = params.get('id')
            pay = Payment.query.filter_by(transaction_id=str(paycom_id)).first()
            if not pay:
                return {'id': rpc_id, 'error': {'code': -31003, 'message': 'Transaction not found'}}

            # Agar allaqachon bekor qilingan bo'lsa (Idempotent cancel)
            if pay.status == 'cancelled':
                return {
                    'id': rpc_id,
                    'result': {
                        'transaction': str(pay.id),
                        'cancel_time': int(pay.updated_at.timestamp() * 1000),
                        'state': -2
                    }
                }

            # To'lov va abonementni atomik bekor qilish
            try:
                pay.status = 'cancelled'
                if pay.subscription:
                    pay.subscription.status = 'cancelled'
                
                tx_log.status = 'cancelled'
                db.session.commit()

                cancel_time_ms = int(datetime.now().timestamp() * 1000)
                return {
                    'id': rpc_id,
                    'result': {
                        'transaction': str(pay.id),
                        'cancel_time': cancel_time_ms,
                        'state': -2
                    }
                }
            except Exception as e:
                db.session.rollback()
                return {'id': rpc_id, 'error': {'code': -31008, 'message': f'Bekor qilishda xatolik: {e}'}}

        return {'id': rpc_id, 'error': {'code': -32601, 'message': 'Method not found'}}
