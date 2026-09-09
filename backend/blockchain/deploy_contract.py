import os
import sys
import json
import logging

# Ensure backend directory is in sys.path when running standalone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blockchain.web3_config import get_web3_provider, load_contract_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deploy_contract")

def deploy():
    w3, rpc_url = get_web3_provider()
    
    if not w3.is_connected():
        logger.error(f"Cannot connect to Ganache blockchain network at: {rpc_url}. Deploy halted.")
        return False
        
    logger.info(f"Connected to Ganache at {rpc_url}")
    
    # Load ABI and bytecode from local compiled artifact
    dir_path = os.path.dirname(os.path.abspath(__file__))
    compiled_path = os.path.join(dir_path, "contract_compiled.json")
    
    if not os.path.exists(compiled_path):
        logger.error(f"Compiled contract json not found at {compiled_path}. Run scratch_compile.py first.")
        return False
        
    try:
        with open(compiled_path, "r") as f:
            contract_data = json.load(f)
            abi = contract_data["abi"]
            bytecode = contract_data["bytecode"]
    except Exception as e:
        logger.error(f"Error reading compilation data: {e}")
        return False
        
    # Get deployment account (use first Ganache account)
    accounts = w3.eth.accounts
    if not accounts:
        logger.error("No Ethereum accounts found on connected Ganache provider.")
        return False
        
    deployer = accounts[0]
    logger.info(f"Deploying SecurityAudit contract from account: {deployer}")
    
    try:
        # Create contract object
        SecurityAudit = w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Build transaction
        tx_hash = SecurityAudit.constructor().transact({
            "from": deployer,
            "gas": 3000000
        })
        
        # Wait for transaction receipt
        logger.info("Waiting for transaction confirmation...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        contract_address = tx_receipt.contractAddress
        logger.info(f"Smart Contract successfully deployed at address: {contract_address}")
        
        # Save deployed address
        addr_path = os.path.join(dir_path, "deployed_address.json")
        with open(addr_path, "w") as f:
            json.dump({"address": contract_address}, f, indent=2)
            
        logger.info(f"Deployed address saved to {addr_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        return False

if __name__ == "__main__":
    deploy()
