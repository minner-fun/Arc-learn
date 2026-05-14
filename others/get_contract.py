from circle.web3 import utils, smart_contract_platform
from dotenv import load_dotenv
import os
import json
load_dotenv()

scpClient = utils.init_smart_contract_platform_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET")
)

api_instance = smart_contract_platform.ViewUpdateApi(scpClient)
contract_response = api_instance.get_contract(
    id=os.getenv("CIRCLE_CONTRACT_ID")
)

print(json.dumps(contract_response.data.to_dict(), indent=2, default=str))