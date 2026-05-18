import time



from circle.web3 import utils, developer_controlled_wallets
import os
from dotenv import load_dotenv

load_dotenv()

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)

# wallet_sets_api = developer_controlled_wallets.WalletSetsApi(circle_client)
# wallets_api = developer_controlled_wallets.WalletsApi(circle_client)

# wallet_set = wallet_sets_api.create_wallet_set(
#     developer_controlled_wallets.CreateWalletSetRequest.from_dict({
#         "name": "ERC8004 Agent Wallets",
#     })
# )
# wallet_set_id = wallet_set.data.wallet_set.actual_instance.id



IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"

METADATA_URI = "ipfs://Qmey7kmWo9TksRPvbA7Q7Hj6FNLXBVbVhayAC8gsfuqwac"

transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)

request = developer_controlled_wallets \
    .CreateContractExecutionTransactionForDeveloperRequest.from_dict({
        "walletAddress": os.getenv("AGENT_OWNER_WALLET_ADDRESS"),
        "blockchain": "ARC-TESTNET",
        "contractAddress": IDENTITY_REGISTRY,
        "abiFunctionSignature": "register(string)",
        "abiParameters": [METADATA_URI],
        "feeLevel": "MEDIUM",
    })

response = transactions_api.create_developer_transaction_contract_execution(request)

# Poll until confirmed
tx_hash = None
for _ in range(30):
    time.sleep(2)
    tx = transactions_api.get_transaction(id=response.data.id)
    if tx.data.transaction.state == "COMPLETE":
        tx_hash = tx.data.transaction.tx_hash
        break
    if tx.data.transaction.state == "FAILED":
        raise Exception("Registration failed")

print(f"Registered: https://testnet.arcscan.app/tx/{tx_hash}")