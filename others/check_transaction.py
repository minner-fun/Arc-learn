from circle.web3 import utils, developer_controlled_wallets
import os
import json
from dotenv import load_dotenv
load_dotenv()


client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET")
)

transaction_id = os.getenv("CIRCLE_TRANSACTION_ID")
if not transaction_id:
    raise SystemExit(
        "CIRCLE_TRANSACTION_ID is missing. Set it in .env to the transaction UUID "
        "(from deploy_erc20.py output or Developer Console -> Wallets -> Transactions)."
    )

api_instance = developer_controlled_wallets.TransactionsApi(client)
transaction_response = api_instance.get_transaction(id=transaction_id)

print(json.dumps(transaction_response.data.to_dict(), indent=2, default=str))