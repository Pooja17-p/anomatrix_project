import time
import logging
import threading
from datetime import datetime
from config import db
from blockchain.web3_config import get_web3_provider, get_contract_instance

logger = logging.getLogger("blockchain_service")
logger.setLevel(logging.INFO)

# Global lock for thread safety
blockchain_lock = threading.Lock()

def check_blockchain_availability():
    """
    Checks if connection to local Ganache is alive and contract is reachable.
    """
    try:
        w3, _ = get_web3_provider()
        if not w3.is_connected():
            return False
        contract = get_contract_instance(w3)
        return contract is not None
    except Exception:
        return False

def add_blockchain_audit_log(
    user_id,
    event_type,
    timestamp,
    ip_address,
    city,
    country,
    risk_level,
    auth_method,
    login_status
):
    """
    Attempts to write an audit log to the blockchain.
    If the blockchain is offline, caches the log in MongoDB pending queue.
    Implements retry logic and duplicate prevention.
    """
    # Create the log dictionary
    log_data = {
        "user_id": str(user_id or ""),
        "event_type": str(event_type or ""),
        "timestamp": int(timestamp or time.time()),
        "ip_address": str(ip_address or "127.0.0.1"),
        "city": str(city or "Unknown"),
        "country": str(country or "Unknown"),
        "risk_level": str(risk_level or "Low"),
        "auth_method": str(auth_method or "None"),
        "login_status": str(login_status or "Unknown")
    }

    # Deduplicate logic: check if the exact audit has been queued or posted recently
    existing_pending = db["pending_blockchain_logs"].find_one({
        "user_id": log_data["user_id"],
        "event_type": log_data["event_type"],
        "timestamp": log_data["timestamp"]
    })
    if existing_pending:
        logger.info(f"Duplicate log detected in pending queue: {log_data['event_type']} for {log_data['user_id']}. Skipping.")
        return None

    # Try transaction writing
    w3, rpc_url = get_web3_provider()
    contract = get_contract_instance(w3)
    
    if w3.is_connected() and contract:
        # We have a valid connection
        with blockchain_lock:
            # Use 3 retries
            for attempt in range(1, 4):
                try:
                    accounts = w3.eth.accounts
                    if not accounts:
                        raise ValueError("No accounts loaded in Web3 provider.")
                    
                    deployer = accounts[0]
                    
                    # Estimate gas if possible, or use standard
                    tx_hash = contract.functions.addAuditLog(
                        log_data["user_id"],
                        log_data["event_type"],
                        log_data["timestamp"],
                        log_data["ip_address"],
                        log_data["city"],
                        log_data["country"],
                        log_data["risk_level"],
                        log_data["auth_method"],
                        log_data["login_status"]
                    ).transact({
                        "from": deployer,
                        "gas": 1000000
                    })
                    
                    # Verify transaction success
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
                    if receipt and receipt.status == 1:
                        tx_hash_hex = "0x" + receipt.transactionHash.hex()
                        logger.info(f"[BLOCKCHAIN SUCCESS] Logged '{event_type}' to blockchain. Tx: {tx_hash_hex}")
                        return tx_hash_hex
                    else:
                        raise RuntimeError("Transaction reverted on-chain.")
                        
                except Exception as ex:
                    logger.warning(f"Blockchain write attempt {attempt} failed for '{event_type}': {ex}")
                    time.sleep(1)
            
            logger.error("Failed to write to blockchain after 3 attempts. Queueing locally.")

    # Queue locally in MongoDB since Blockchain is offline/failed
    try:
        db["pending_blockchain_logs"].insert_one(log_data)
        logger.info(f"[OFFLINE QUEUE] Logged '{event_type}' offline in MongoDB pending queue.")
    except Exception as mongo_err:
        logger.critical(f"Failed to queue log to MongoDB pending queue: {mongo_err}")
        
    return None

# Background Synchronizer daemon
def run_sync_daemon():
    """
    Background worker function that polls Ganache connectivity and drains the pending queue.
    """
    logger.info("Blockchain offline sync daemon thread started.")
    while True:
        try:
            time.sleep(10)
            
            # Check queue size
            pending_count = db["pending_blockchain_logs"].count_documents({})
            if pending_count == 0:
                continue
                
            w3, _ = get_web3_provider()
            contract = get_contract_instance(w3)
            
            if w3.is_connected() and contract:
                logger.info(f"[SYNC DAEMON] Blockchain is online. Found {pending_count} pending audit logs to sync.")
                
                # Fetch pending logs sorted by timestamp
                pending_logs = list(db["pending_blockchain_logs"].find().sort("timestamp", 1))
                
                for log in pending_logs:
                    mongo_id = log["_id"]
                    
                    try:
                        accounts = w3.eth.accounts
                        if not accounts:
                            raise ValueError("No accounts loaded.")
                        deployer = accounts[0]
                        
                        tx_hash = contract.functions.addAuditLog(
                            log["user_id"],
                            log["event_type"],
                            log["timestamp"],
                            log["ip_address"],
                            log["city"],
                            log["country"],
                            log["risk_level"],
                            log["auth_method"],
                            log["login_status"]
                        ).transact({
                            "from": deployer,
                            "gas": 1000000
                        })
                        
                        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)
                        if receipt and receipt.status == 1:
                            tx_hash_hex = "0x" + receipt.transactionHash.hex()
                            logger.info(f"[SYNC SUCCESS] Synced pending log {mongo_id} to blockchain. Tx: {tx_hash_hex}")
                            
                            # Update original login history record (if matching)
                            db["login_history"].update_one(
                                {
                                    "username": log["user_id"],
                                    "event_type": log["event_type"],
                                    "timestamp": datetime.fromtimestamp(log["timestamp"])
                                },
                                {"$set": {"blockchain_transaction_hash": tx_hash_hex}}
                            )
                            
                            # Remove from queue
                            db["pending_blockchain_logs"].delete_one({"_id": mongo_id})
                        else:
                            raise RuntimeError("Sync transaction reverted.")
                            
                    except Exception as tx_err:
                        logger.error(f"[SYNC ERROR] Failed to sync log {mongo_id}: {tx_err}. Pausing sync.")
                        break # Pause sync loop until next check interval
                        
        except Exception as e:
            logger.error(f"Sync daemon encountered unexpected error: {e}")

# Start Sync Daemon immediately on load
daemon_thread = threading.Thread(target=run_sync_daemon, daemon=True)
daemon_thread.start()
