from circle.web3 import utils, smart_contract_platform
import os
import json
from dotenv import load_dotenv
load_dotenv()

scpClient = utils.init_smart_contract_platform_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET")
)

api_instance = smart_contract_platform.TemplatesApi(scpClient)

request = smart_contract_platform.TemplateContractDeploymentRequest.from_dict({
    "blockchain": "ARC-TESTNET",
    "name": "MyTokenContract",
    "walletId": os.getenv("CIRCLE_WALLET_ID"),
    "templateParameters": {
        "name": "MyToken",
        "symbol": "MTK",
        "defaultAdmin": os.getenv("CIRCLE_WALLET_ADDRESS"),
        "primarySaleRecipient": os.getenv("CIRCLE_WALLET_ADDRESS"),
    },
    "feeLevel": "MEDIUM"
})

response = api_instance.deploy_contract_template("a1b74add-23e0-4712-88d1-6b3009e85a86", request)

print(json.dumps(response.data.to_dict(), indent=2))