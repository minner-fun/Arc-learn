from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv()

IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"

RPC_URL = "https://rpc.testnet.arc.network/"
w3 = Web3(Web3.HTTPProvider(RPC_URL))




REPUTATION_REGISTRY = "0x8004B663056A597Dffe9eCcC1965A193B7388713"

tag = "successful_trade"
feedback_hash = "0x" + w3.keccak(text=tag).hex()

request = developer_controlled_wallets \
    .CreateContractExecutionTransactionForDeveloperRequest.from_dict({
        "walletAddress": validator_wallet.address,
        "blockchain": "ARC-TESTNET",
        "contractAddress": REPUTATION_REGISTRY,
        "abiFunctionSignature":
            "giveFeedback(uint256,int128,uint8,string,string,string,string,bytes32)",
        "abiParameters": [
            str(agent_id), "95", "0", tag, "", "", "", feedback_hash
        ],
        "feeLevel": "MEDIUM",
    })

response = transactions_api.create_developer_transaction_contract_execution(request)

# Poll until confirmed (same pattern as Step 4)