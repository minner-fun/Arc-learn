from circle.web3 import utils, developer_controlled_wallets
from web3 import Web3
import os
import time
from dotenv import load_dotenv

load_dotenv()

IDENTITY_REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
REPUTATION_REGISTRY = "0x8004B663056A597Dffe9eCcC1965A193B7388713"
VALIDATION_REGISTRY = "0x8004Cb1BF31DAf7788923b405b754f57acEB4272"
RPC_URL = "https://rpc.testnet.arc.network/"

METADATA_URI = os.getenv("METADATA_URI") or \
    "ipfs://bafkreibdi6623n3xpf7ymk62ckb4bo75o3qemwkpfvp5i25j66itxvsoei"

circle_client = utils.init_developer_controlled_wallets_client(
    api_key=os.getenv("CIRCLE_API_KEY"),
    entity_secret=os.getenv("CIRCLE_ENTITY_SECRET"),
)

wallet_sets_api = developer_controlled_wallets.WalletSetsApi(circle_client)
wallets_api = developer_controlled_wallets.WalletsApi(circle_client)
transactions_api = developer_controlled_wallets.TransactionsApi(circle_client)

w3 = Web3(Web3.HTTPProvider(RPC_URL))


def wait_for_transaction(tx_id: str, label: str) -> str:
    print(f"  Waiting for {label}", end="", flush=True)
    for _ in range(30):
        time.sleep(2)
        tx = transactions_api.get_transaction(id=tx_id)
        state = tx.data.transaction.state
        if state == "COMPLETE":
            tx_hash = tx.data.transaction.tx_hash
            print(f" ✓\n  Tx: https://testnet.arcscan.app/tx/{tx_hash}")
            return tx_hash
        if state == "FAILED":
            raise Exception(f"{label} failed onchain")
        print(".", end="", flush=True)
    raise Exception(f"{label} timed out")


def send_contract_tx(wallet_address, address, sig, params, label):
    request = developer_controlled_wallets \
        .CreateContractExecutionTransactionForDeveloperRequest.from_dict({
            "walletAddress": wallet_address,
            "blockchain": "ARC-TESTNET",
            "contractAddress": address,
            "abiFunctionSignature": sig,
            "abiParameters": params,
            "feeLevel": "MEDIUM",
        })
    response = transactions_api.create_developer_transaction_contract_execution(request)
    return wait_for_transaction(response.data.id, label)


def main():
    # Step 1: Create wallets
    # print("\n── Step 1: Create wallets ──")

    # wallet_set = wallet_sets_api.create_wallet_set(
    #     developer_controlled_wallets.CreateWalletSetRequest.from_dict({
    #         "name": "ERC8004 Agent Wallets",
    #     })
    # )
    # wallet_set_id = wallet_set.data.wallet_set.actual_instance.id

    # wallets_response = wallets_api.create_wallet(
    #     developer_controlled_wallets.CreateWalletRequest.from_dict({
    #         "blockchains": ["ARC-TESTNET"],
    #         "count": 2,
    #         "walletSetId": wallet_set_id,
    #         "accountType": "SCA",
    #     })
    # )

    # owner_wallet = wallets_response.data.wallets[0].actual_instance
    # validator_wallet = wallets_response.data.wallets[1].actual_instance

    # print(f"  Owner:     {owner_wallet.address} ({owner_wallet.id})")
    # print(f"  Validator: {validator_wallet.address} ({validator_wallet.id})")

    owner_wallet_address = os.getenv("AGENT_OWNER_WALLET_ADDRESS")
    validator_wallet_address = os.getenv("AGENT_VALIDATOR_WALLET_ADDRESS")

    # Step 2: Register agent identity
    print("\n── Step 2: Register agent identity ──")
    print(f"  Metadata URI: {METADATA_URI}")

    send_contract_tx(
        owner_wallet_address, IDENTITY_REGISTRY,
        "register(string)", [METADATA_URI], "registration",
    )

    # Step 3: Retrieve agent ID
    print("\n── Step 3: Retrieve agent ID ──")

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
        argument_filters={"to": owner_wallet_address},
    ).get_all_entries()

    if not events:
        raise Exception("No Transfer events found — registration may have failed")

    agent_id = events[-1]["args"]["tokenId"]
    on_chain_owner = identity_contract.functions.ownerOf(agent_id).call()
    token_uri = identity_contract.functions.tokenURI(agent_id).call()

    print(f"  Agent ID:     {agent_id}")
    print(f"  Owner:        {on_chain_owner}")
    print(f"  Metadata URI: {token_uri}")

    # Step 4: Record reputation
    print("\n── Step 4: Record reputation ──")

    tag = "successful_trade"
    feedback_hash = "0x" + w3.keccak(text=tag).hex()

    send_contract_tx(
        validator_wallet_address, REPUTATION_REGISTRY,
        "giveFeedback(uint256,int128,uint8,string,string,string,string,bytes32)",
        [str(agent_id), "95", "0", tag, "", "", "", feedback_hash],
        "reputation",
    )

    # Step 5: Verify reputation
    print("\n── Step 5: Verify reputation ──")

    reputation_logs = w3.eth.get_logs({
        "address": REPUTATION_REGISTRY,
        "fromBlock": max(0, latest_block - 1000),
        "toBlock": "latest",
    })

    print(f"  Found {len(reputation_logs)} feedback event(s)")

    # Step 6: Request validation (owner requests; validator responds per ERC-8004)
    print("\n── Step 6: Request validation ──")

    request_uri = "ipfs://bafkreiexamplevalidationrequest"
    request_hash = "0x" + w3.keccak(text=f"kyc_verification_request_agent_{agent_id}").hex()

    send_contract_tx(
        owner_wallet_address, VALIDATION_REGISTRY,
        "validationRequest(address,uint256,string,bytes32)",
        [validator_wallet_address, str(agent_id), request_uri, request_hash],
        "validation request",
    )

    # Step 7: Validation response (validator responds; 100 = passed, 0 = failed)
    print("\n── Step 7: Validation response ──")

    send_contract_tx(
        validator_wallet_address, VALIDATION_REGISTRY,
        "validationResponse(bytes32,uint8,string,bytes32,string)",
        [request_hash, "100", "", "0x" + "0" * 64, "kyc_verified"],
        "validation response",
    )

    # Step 8: Check validation status
    print("\n── Step 8: Check validation ──")

    validation_abi = [{
        "inputs": [{"name": "requestHash", "type": "bytes32"}],
        "name": "getValidationStatus",
        "outputs": [
            {"name": "validatorAddress", "type": "address"},
            {"name": "agentId", "type": "uint256"},
            {"name": "response", "type": "uint8"},
            {"name": "responseHash", "type": "bytes32"},
            {"name": "tag", "type": "string"},
            {"name": "lastUpdate", "type": "uint256"},
        ],
        "stateMutability": "view",
        "type": "function",
    }]

    validation_contract = w3.eth.contract(
        address=VALIDATION_REGISTRY, abi=validation_abi
    )

    val_addr, _, val_response, _, val_tag, _ = \
        validation_contract.functions.getValidationStatus(
            bytes.fromhex(request_hash[2:])
        ).call()

    print(f"  Validator:  {val_addr}")
    print(f"  Response:   {val_response} (100 = passed)")
    print(f"  Tag:        {val_tag}")

    print("\n── Complete ──")
    print("  ✓ Identity registered")
    print("  ✓ Reputation recorded")
    print("  ✓ Validation requested and verified")
    print(f"\n  Explorer: https://testnet.arcscan.app/address/{owner_wallet_address}\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"\nError: {error}")
        exit(1)