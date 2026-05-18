from web3 import Web3
import os
from dotenv import load_dotenv
load_dotenv()

IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"

RPC_URL = "https://rpc.testnet.arc.network/"
w3 = Web3(Web3.HTTPProvider(RPC_URL))

identity_abi = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": True, "name": "tokenId", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "ownerOf",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "tokenId", "type": "uint256"}],
        "name": "tokenURI",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function",
    },
]

identity_contract = w3.eth.contract(address=IDENTITY_REGISTRY, abi=identity_abi)

latest_block = w3.eth.block_number
from_block = max(0, latest_block - 10000)
events = identity_contract.events.Transfer.create_filter(
    from_block=from_block,
    to_block=latest_block,
    argument_filters={"to": os.getenv("AGENT_OWNER_WALLET_ADDRESS")},
).get_all_entries()

agent_id = events[-1]["args"]["tokenId"]
on_chain_owner = identity_contract.functions.ownerOf(agent_id).call()
token_uri = identity_contract.functions.tokenURI(agent_id).call()

print(f"Agent ID: {agent_id}")
print(f"Owner: {on_chain_owner}")
print(f"Metadata: {token_uri}")