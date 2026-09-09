import os
import json
import logging

logger = logging.getLogger("web3_config")
logger.setLevel(logging.INFO)

try:
    from web3 import Web3
    HAS_WEB3 = True
except Exception as e:
    logger.warning(f"Web3 package could not be loaded: {e}")
    Web3 = None
    HAS_WEB3 = False

class DummyWeb3:
    def is_connected(self):
        return False

# Default configuration parameters
DEFAULT_RPC_URL = "http://127.0.0.1:8545"

def get_web3_provider():
    """
    Get connection to Ganache Ethereum node.
    Loads GANACHE_URL from environment or uses default port 8545.
    """
    if not HAS_WEB3 or Web3 is None:
        return DummyWeb3(), DEFAULT_RPC_URL
    try:
        rpc_url = os.environ.get("GANACHE_URL") or os.environ.get("BLOCKCHAIN_URL") or DEFAULT_RPC_URL
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        return w3, rpc_url
    except Exception as e:
        logger.error(f"Error creating Web3 provider: {e}")
        return DummyWeb3(), DEFAULT_RPC_URL

def load_contract_data():
    """
    Loads contract ABI and deployed address.
    """
    dir_path = os.path.dirname(os.path.abspath(__file__))
    
    # Load ABI/bytecode
    abi_path = os.path.join(dir_path, "contract_compiled.json")
    abi_data = []
    if os.path.exists(abi_path):
        try:
            with open(abi_path, "r") as f:
                data = json.load(f)
                abi_data = data.get("abi", [])
        except Exception as e:
            logger.error(f"Error loading contract compilation data: {e}")
            
    # Load Address
    addr_path = os.path.join(dir_path, "deployed_address.json")
    contract_address = None
    if os.path.exists(addr_path):
        try:
            with open(addr_path, "r") as f:
                data = json.load(f)
                contract_address = data.get("address")
        except Exception as e:
            logger.error(f"Error loading deployed address: {e}")
            
    return abi_data, contract_address

def get_contract_instance(w3=None):
    """
    Returns a configured Web3 contract instance if connected and deployed.
    """
    if w3 is None:
        w3, _ = get_web3_provider()
        
    abi, address = load_contract_data()
    if not address or not w3.is_connected():
        return None
        
    try:
        # Check if address is valid hex and has code
        checksum_address = w3.to_checksum_address(address)
        code = w3.eth.get_code(checksum_address)
        if len(code) > 0:
            return w3.eth.contract(address=checksum_address, abi=abi)
    except Exception as e:
        logger.error(f"Error instantiating smart contract: {e}")
        
    return None
