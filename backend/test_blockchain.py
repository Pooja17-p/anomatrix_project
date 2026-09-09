import sys
import os
import time
import subprocess
import unittest
from datetime import datetime

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure test environment variables before import
os.environ["GANACHE_URL"] = "http://127.0.0.1:8555"

from app import app
from config import db
from blockchain.web3_config import get_web3_provider, get_contract_instance, load_contract_data
from blockchain.deploy_contract import deploy
from blockchain.blockchain_service import (
    add_blockchain_audit_log,
    check_blockchain_availability,
)

def kill_process_tree(process):
    if not process:
        return
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            process.terminate()
            process.wait()
    except Exception as e:
        print(f"Error killing process: {e}")

class TestBlockchainSecurityLogging(unittest.TestCase):
    ganache_process = None

    @classmethod
    def setUpClass(cls):
        print("\n=== STARTING LOCAL TEST GANACHE NODE ON PORT 8555 ===")
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        cls.ganache_process = subprocess.Popen(
            [npx_cmd, "--yes", "ganache", "-p", "8555", "--wallet.totalAccounts", "5"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # Give Ganache time to spin up (increased to 8 seconds for slower environments)
        time.sleep(8)
        
        # Deploy contract
        print("Deploying SecurityAudit smart contract...")
        success = deploy()
        if not success:
            raise RuntimeError("Failed to deploy smart contract on test Ganache node.")

    @classmethod
    def tearDownClass(cls):
        print("\n=== TEARING DOWN TEST GANACHE NODE ===")
        if cls.ganache_process:
            kill_process_tree(cls.ganache_process)
            
        # Clean up deployed address file
        dir_path = os.path.dirname(os.path.abspath(__file__))
        addr_path = os.path.join(dir_path, "blockchain", "deployed_address.json")
        if os.path.exists(addr_path):
            try:
                os.remove(addr_path)
            except:
                pass

    def setUp(self):
        self.client = app.test_client()
        self.test_user = "blockchain_test_user_2026"
        db["login_history"].delete_many({"username": self.test_user})
        db["pending_blockchain_logs"].delete_many({"user_id": self.test_user})

    def tearDown(self):
        db["login_history"].delete_many({"username": self.test_user})
        db["pending_blockchain_logs"].delete_many({"user_id": self.test_user})

    def test_blockchain_connection(self):
        print("\n--- 1. Testing Web3 Node Connection & Smart Contract Load ---")
        w3, rpc_url = get_web3_provider()
        self.assertTrue(w3.is_connected())
        self.assertEqual(rpc_url, "http://127.0.0.1:8555")
        
        contract = get_contract_instance(w3)
        self.assertIsNotNone(contract)
        print("Connected to blockchain and contract successfully loaded.")

    def test_blockchain_audit_logging_success(self):
        print("\n--- 2. Testing On-Chain Audit Logging Success ---")
        timestamp_sec = int(time.time())
        tx_hash = add_blockchain_audit_log(
            user_id=self.test_user,
            event_type="User Login",
            timestamp=timestamp_sec,
            ip_address="8.8.8.8",
            city="Ashburn",
            country="United States",
            risk_level="Low",
            auth_method="Password",
            login_status="Successful"
        )
        
        # Verify transaction returns a valid tx hash
        self.assertIsNotNone(tx_hash)
        self.assertTrue(tx_hash.startswith("0x"))
        self.assertEqual(len(tx_hash), 66) # 0x + 64 hex characters
        print(f"Audit log saved on-chain successfully. Tx Hash: {tx_hash}")

        # Check `/api/blockchain/logs` response
        resp = self.client.get("/api/blockchain/logs")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("logs", data)
        self.assertGreaterEqual(data["count"], 1)
        
        # Verify first element is our log (reverse order)
        matched_log = None
        for log in data["logs"]:
            if log["user_id"] == self.test_user:
                matched_log = log
                break
                
        self.assertIsNotNone(matched_log)
        self.assertEqual(matched_log["event_type"], "User Login")
        self.assertEqual(matched_log["city"], "Ashburn")
        print("Logged values match contract getter values successfully.")

    def test_blockchain_offline_queueing(self):
        print("\n--- 3. Testing Offline Queueing when Blockchain goes Down ---")
        # Terminate Ganache
        if self.__class__.ganache_process:
            kill_process_tree(self.__class__.ganache_process)
        
        # Check connectivity is false
        self.assertFalse(check_blockchain_availability())
        print("Ganache simulated shutdown confirmed.")

        # Trigger audit log - should fail gracefully and queue
        timestamp_sec = int(time.time())
        tx_hash = add_blockchain_audit_log(
            user_id=self.test_user,
            event_type="Suspicious Login",
            timestamp=timestamp_sec,
            ip_address="24.48.0.1",
            city="Montreal",
            country="Canada",
            risk_level="High",
            auth_method="Password",
            login_status="Challenged"
        )
        
        # Should return None because blockchain is offline
        self.assertIsNone(tx_hash)
        
        # Verify that record was queued in MongoDB pending queue
        pending_record = db["pending_blockchain_logs"].find_one({"user_id": self.test_user})
        self.assertIsNotNone(pending_record)
        self.assertEqual(pending_record["event_type"], "Suspicious Login")
        self.assertEqual(pending_record["city"], "Montreal")
        print("Blockchain failure caught gracefully. Log queued to local MongoDB collection.")

        # Restart Ganache for cleanup/sync (and other tests)
        print("Restarting Ganache node on port 8555...")
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        self.__class__.ganache_process = subprocess.Popen(
            [npx_cmd, "--yes", "ganache", "-p", "8555", "--wallet.totalAccounts", "5"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(8)
        
        # Re-deploy contract
        deploy()
        self.assertTrue(check_blockchain_availability())
        print("Ganache restarted and connection re-established.")

if __name__ == "__main__":
    unittest.main()
