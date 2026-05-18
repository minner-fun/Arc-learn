from circle.web3 import utils, developer_controlled_wallets
import os
import json
from dotenv import load_dotenv
load_dotenv()

client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET")
)

api_instance = developer_controlled_wallets.TransactionsApi(client)

mint_request = developer_controlled_wallets.CreateContractExecutionTransactionForDeveloperRequest.from_dict({
    "walletId": os.getenv("CIRCLE_WALLET_ID"),
    "abiFunctionSignature": "mintTo(address,uint256)",
    "abiParameters": [
        os.getenv("RECIPIENT_WALLET_ADDRESS"),
        "1000000000000000000"
    ],
    "contractAddress": os.getenv("CIRCLE_ERC20_ADDRESS"),
    "feeLevel": "MEDIUM",
})

mint_response = api_instance.create_developer_transaction_contract_execution(mint_request)

print(json.dumps(mint_response.data.to_dict(), indent=2))