import os
import json
import solcx

try:
    print("Installing solc compiler...")
    solcx.install_solc("0.8.20")
    solcx.set_solc_version("0.8.20")
    
    contract_path = os.path.join(os.path.dirname(__file__), "SecurityAudit.sol")
    print(f"Compiling contract {contract_path}...")
    
    compiled_sol = solcx.compile_files(
        [contract_path],
        output_values=["abi", "bin"]
    )
    
    # Print keys to see exact structure
    print("Compiled keys:", list(compiled_sol.keys()))
    
    # Try to find SecurityAudit in any key
    contract_interface = None
    for k, v in compiled_sol.items():
        if "SecurityAudit" in k:
            contract_interface = v
            print(f"Found contract interface key: {k}")
            break
            
    if not contract_interface:
        raise KeyError("SecurityAudit contract not found in compiled output keys.")
        
    # Save the output to JSON
    output_path = os.path.join(os.path.dirname(__file__), "contract_compiled.json")
    with open(output_path, "w") as f:
        json.dump({
            "abi": contract_interface["abi"],
            "bytecode": contract_interface["bin"]
        }, f, indent=2)
        
    print(f"Contract compiled and saved to {output_path} successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
