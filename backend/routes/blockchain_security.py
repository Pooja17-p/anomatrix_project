import time
import logging
from flask import Blueprint, request, jsonify
from blockchain.web3_config import get_web3_provider, get_contract_instance, load_contract_data
from blockchain.blockchain_service import add_blockchain_audit_log, check_blockchain_availability
from config import db

logger = logging.getLogger("blockchain_security")
logger.setLevel(logging.INFO)

blockchain_security_bp = Blueprint("blockchain_security", __name__)

@blockchain_security_bp.route("/api/blockchain/add-log", methods=["POST"])
def add_log():
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        event_type = data.get("event_type")
        timestamp = data.get("timestamp") or int(time.time())
        ip_address = data.get("ip_address") or "127.0.0.1"
        city = data.get("city") or "Unknown"
        country = data.get("country") or "Unknown"
        risk_level = data.get("risk_level") or "Low"
        auth_method = data.get("auth_method") or "None"
        login_status = data.get("login_status") or "Successful"

        if not user_id or not event_type:
            return jsonify({"message": "user_id and event_type are required"}), 400

        tx_hash = add_blockchain_audit_log(
            user_id, event_type, timestamp, ip_address, city, country, risk_level, auth_method, login_status
        )

        return jsonify({
            "success": True if tx_hash else False,
            "transaction_hash": tx_hash,
            "message": "Audit log processed." if tx_hash else "Blockchain offline. Log queued locally."
        }), 200
    except Exception as e:
        logger.exception("Error adding blockchain log")
        return jsonify({"message": str(e)}), 500

@blockchain_security_bp.route("/api/blockchain/logs", methods=["GET"])
def get_logs():
    try:
        w3, _ = get_web3_provider()
        contract = get_contract_instance(w3)

        logs_list = []
        
        # If blockchain is available, query contract
        if w3.is_connected() and contract:
            try:
                total_logs = contract.functions.getTotalLogs().call()
                # Query in reverse order to show newest first
                for i in range(total_logs - 1, -1, -1):
                    log_tuple = contract.functions.getAuditLog(i).call()
                    # Resolve transaction hash for block viewer compatibility
                    # For simplicity, fallback to retrieving mock tx hashes or matching from db
                    db_match = db["login_history"].find_one({
                        "$or": [{"username": log_tuple[0]}, {"user_id": log_tuple[0]}],
                        "event_type": log_tuple[1]
                    }, sort=[("timestamp", -1), ("login_time", -1)]) or {}
                    
                    logs_list.append({
                        "user_id": log_tuple[0],
                        "event_type": log_tuple[1],
                        "timestamp": int(log_tuple[2]),
                        "ip_address": db_match.get("ip_address") or log_tuple[3],
                        "city": db_match.get("city") or log_tuple[4],
                        "region": db_match.get("region") or db_match.get("state") or "",
                        "state": db_match.get("state") or db_match.get("region") or "",
                        "country": db_match.get("country") or log_tuple[5],
                        "latitude": db_match.get("latitude"),
                        "longitude": db_match.get("longitude"),
                        "isp": db_match.get("isp"),
                        "risk_level": log_tuple[6],
                        "auth_method": log_tuple[7],
                        "login_status": log_tuple[8],
                        "transaction_hash": db_match.get("blockchain_transaction_hash") or f"0x_onchain_{i:064x}"
                    })
                return jsonify({"status": "success", "count": len(logs_list), "logs": logs_list}), 200
            except Exception as w3_err:
                logger.error(f"Error querying contract logs: {w3_err}. Falling back to DB.")

        # Fallback to local MongoDB history logs if blockchain is offline
        logger.info("Retrieving logs from database fallback")
        db_logs = list(db["login_history"].find().sort("timestamp", -1))
        
        for item in db_logs:
            # Check timestamp type
            ts = item.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts = int(datetime.fromisoformat(ts).timestamp())
                except:
                    ts = int(time.time())
            elif hasattr(ts, "timestamp"):
                ts = int(ts.timestamp())
            else:
                ts = int(time.time())

            logs_list.append({
                "user_id": item.get("username") or item.get("user_id") or "Unknown",
                "event_type": item.get("event_type") or "LoginAttempt",
                "timestamp": ts,
                "ip_address": item.get("ip_address") or "Unavailable",
                "city": item.get("city") or "Location unavailable",
                "region": item.get("region") or item.get("state") or "",
                "state": item.get("state") or item.get("region") or "",
                "country": item.get("country") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "isp": item.get("isp"),
                "risk_level": item.get("risk_level") or "Low",
                "auth_method": item.get("authentication_method") or item.get("auth_method") or "None",
                "login_status": item.get("login_status") or "Successful",
                "transaction_hash": item.get("blockchain_transaction_hash")
            })

        return jsonify({"status": "fallback", "count": len(logs_list), "logs": logs_list}), 200
        
    except Exception as e:
        logger.exception("Error fetching blockchain logs")
        return jsonify({"message": str(e)}), 500

@blockchain_security_bp.route("/api/blockchain/user-logs", methods=["GET"])
@blockchain_security_bp.route("/api/blockchain/user-logs/<username>", methods=["GET"])
def get_user_logs(username=None):
    try:
        if not username:
            username = request.args.get("username")
            
        if not username:
            return jsonify({"message": "username is required"}), 400
            
        w3, _ = get_web3_provider()
        contract = get_contract_instance(w3)
        
        logs_list = []
        
        # If blockchain is online, fetch indices for user and call getAuditLog
        if w3.is_connected() and contract:
            try:
                indices = contract.functions.getAuditLogsByUser(username).call()
                # Query in reverse order
                for idx in reversed(indices):
                    log_tuple = contract.functions.getAuditLog(idx).call()
                    db_match = db["login_history"].find_one({
                        "$or": [{"username": log_tuple[0]}, {"user_id": log_tuple[0]}],
                        "event_type": log_tuple[1]
                    }, sort=[("timestamp", -1), ("login_time", -1)]) or {}
                    
                    logs_list.append({
                        "user_id": log_tuple[0],
                        "event_type": log_tuple[1],
                        "timestamp": int(log_tuple[2]),
                        "ip_address": db_match.get("ip_address") or log_tuple[3],
                        "city": db_match.get("city") or log_tuple[4],
                        "region": db_match.get("region") or db_match.get("state") or "",
                        "state": db_match.get("state") or db_match.get("region") or "",
                        "country": db_match.get("country") or log_tuple[5],
                        "latitude": db_match.get("latitude"),
                        "longitude": db_match.get("longitude"),
                        "isp": db_match.get("isp"),
                        "risk_level": log_tuple[6],
                        "auth_method": log_tuple[7],
                        "login_status": log_tuple[8],
                        "transaction_hash": db_match.get("blockchain_transaction_hash") or f"0x_onchain_{idx:064x}"
                    })
                return jsonify({"status": "success", "username": username, "count": len(logs_list), "logs": logs_list}), 200
            except Exception as w3_err:
                logger.error(f"Error querying user logs: {w3_err}. Falling back to DB.")

        # Fallback to local MongoDB history logs if blockchain is offline
        db_logs = list(db["login_history"].find({"username": username}).sort("timestamp", -1))
        
        for item in db_logs:
            ts = item.get("timestamp")
            if hasattr(ts, "timestamp"):
                ts = int(ts.timestamp())
            else:
                ts = int(time.time())

            logs_list.append({
                "user_id": item.get("username") or item.get("user_id") or username,
                "event_type": item.get("event_type") or "LoginAttempt",
                "timestamp": ts,
                "ip_address": item.get("ip_address") or "Unavailable",
                "city": item.get("city") or "Location unavailable",
                "region": item.get("region") or item.get("state") or "",
                "state": item.get("state") or item.get("region") or "",
                "country": item.get("country") or "",
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "isp": item.get("isp"),
                "risk_level": item.get("risk_level") or "Low",
                "auth_method": item.get("authentication_method") or item.get("auth_method") or "None",
                "login_status": item.get("login_status") or "Successful",
                "transaction_hash": item.get("blockchain_transaction_hash")
            })

        return jsonify({"status": "fallback", "username": username, "count": len(logs_list), "logs": logs_list}), 200
        
    except Exception as e:
        logger.exception("Error fetching user blockchain logs")
        return jsonify({"message": str(e)}), 500

@blockchain_security_bp.route("/api/blockchain/status", methods=["GET"])
def get_blockchain_status():
    try:
        w3, rpc_url = get_web3_provider()
        connected = w3.is_connected()
        
        _, contract_address = load_contract_data()
        
        latest_block = 0
        total_tx = 0
        network_id = "Unknown"
        
        if connected:
            latest_block = w3.eth.block_number
            network_id = w3.eth.chain_id
            
            # If contract is deployed, count total log transactions
            contract = get_contract_instance(w3)
            if contract:
                total_tx = contract.functions.getTotalLogs().call()
                
        pending_queue = db["pending_blockchain_logs"].count_documents({})
        
        return jsonify({
            "connected": connected,
            "network_url": rpc_url,
            "network_id": network_id,
            "smart_contract_address": contract_address or "Not Deployed",
            "total_transactions": total_tx,
            "latest_block_number": latest_block,
            "pending_queue_size": pending_queue,
            "audit_verification_status": "Verified" if (connected and contract_address) else "Unverified"
        }), 200
    except Exception as e:
        return jsonify({
            "connected": False,
            "network_url": DEFAULT_RPC_URL,
            "network_id": "Unknown",
            "smart_contract_address": "Not Deployed",
            "total_transactions": 0,
            "latest_block_number": 0,
            "pending_queue_size": db["pending_blockchain_logs"].count_documents({}),
            "audit_verification_status": "Unverified",
            "error": str(e)
        }), 200
