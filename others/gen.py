from circle.web3 import utils
import os
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("CIRCLE_CONSOLE_KEY")
ENTITY_SECRET = os.getenv("CIRCLE_ENTITY_SECRET")

def generate_entity_secret():
    entity_secret = utils.generate_entity_secret()
    print("generate_entity_secret result: ", entity_secret)

def register_entity_secret():
    result = utils.register_entity_secret_ciphertext(
    api_key=API_KEY,
    entity_secret=ENTITY_SECRET,
    recoveryFileDownloadPath="recovery",
    )
    print("register_entity_secret_ciphertext result: ", result)



if __name__ == "__main__":
    # generate_entity_secret()
    register_entity_secret()