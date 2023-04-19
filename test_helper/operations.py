from typing import Tuple, List

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk import account, encoding

from pyteal import compileTeal, Mode

from .account import Account
from .marketplaceContract import approval_program, clear_state_program
from .util import (
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
)

APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""


def getContracts(client: AlgodClient) -> Tuple[bytes, bytes]:
    """Get the compiled TEAL contracts for the order.

    Args:
        client: An algod client that has the ability to compile TEAL programs.

    Returns:
        A tuple of 2 byte strings. The first is the approval program, and the
        second is the clear state program.
    """
    global APPROVAL_PROGRAM
    global CLEAR_STATE_PROGRAM

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = fullyCompileContract(client, approval_program())
        CLEAR_STATE_PROGRAM = fullyCompileContract(client, clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM


def createOrderApp(
    client: AlgodClient,
    sender: Account,
    seller: str,
    nftID: int,
    nftPrice: int,
    nftQuantity: int,
) -> int:
    """Create a new order.

    Args:
        client: An algod client.
        sender: The account that will create the order application.
        seller: The address of the seller that currently holds the NFT being
            ordered.
        nftID: The ID of the NFT being ordered.
        nftPrice: The nftPrice amount of the order. If the order close, the buy amount will
            be refunded to the buyer and the NFT will return to the seller.
    Returns:
        The ID of the newly created order app.
    """
    approval, clear = getContracts(client)

    globalSchema = transaction.StateSchema(num_uints=5, num_byte_slices=2)
    localSchema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    app_args = [
        encoding.decode_address(seller),
        nftID.to_bytes(8, "big"),
        nftPrice.to_bytes(8, "big"),
        nftQuantity.to_bytes(8, "big"), 
    ]

    txn = transaction.ApplicationCreateTxn(
        sender=sender.getAddress(),
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval,
        clear_program=clear,
        global_schema=globalSchema,
        local_schema=localSchema,
        app_args=app_args,
        sp=client.suggested_params(),
    )

    signedTxn = txn.sign(sender.getPrivateKey())

    client.send_transaction(signedTxn)

    response = waitForTransaction(client, signedTxn.get_txid())
    assert response.applicationIndex is not None and response.applicationIndex > 0
    return response.applicationIndex


def sellNFT(
    client: AlgodClient,
    appID: int,
    funder: Account,
    nftHolder: Account,
    nftID: int,
    nftQuantity: int,
) -> None:
    """Finish setting up an order.

    This operation funds the app order escrow account, opts that account into
    the NFT, and sends the NFT to the escrow account, all in one atomic
    transaction group. The order must not have started yet.

    The escrow account requires a total of 0.203 Algos for funding. See the code
    below for a breakdown of this amount.

    Args:
        client: An algod client.
        appID: The app ID of the order.
        funder: The account providing the funding for the escrow account.
        nftHolder: The account holding the NFT.
        nftID: The NFT ID.
        nftAmount: The NFT amount being auctioned. Some NFTs has a total supply
            of 1, while others are fractional NFTs with a greater total supply,
            so use a value that makes sense for the NFT being auctioned.
    """
    appAddr = get_application_address(appID)

    suggestedParams = client.suggested_params()

    fundingAmount = (
        # min account balance
        100_000
        # additional min balance to opt into NFT
        + 100_000
        # 3 * min txn fee
        + 3 * 1_000
    )

    fundAppTxn = transaction.PaymentTxn(
        sender=funder.getAddress(),
        receiver=appAddr,
        amt=fundingAmount,
        sp=suggestedParams,
    )

    sellTxn = transaction.ApplicationCallTxn(
        sender=funder.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=[b"sell"],
        foreign_assets=[nftID],
        sp=suggestedParams,
    )

    fundNftTxn = transaction.AssetTransferTxn(
        sender=nftHolder.getAddress(),
        receiver=appAddr,
        index=nftID,
        amt=nftQuantity,
        sp=suggestedParams,
    )

    transaction.assign_group_id([fundAppTxn, sellTxn, fundNftTxn])

    signedFundAppTxn = fundAppTxn.sign(funder.getPrivateKey())
    signedSellTxn = sellTxn.sign(funder.getPrivateKey())
    signedFundNftTxn = fundNftTxn.sign(nftHolder.getPrivateKey())

    client.send_transactions([signedFundAppTxn, signedSellTxn, signedFundNftTxn])

    waitForTransaction(client, signedFundAppTxn.get_txid())


def buyNft(
        client: AlgodClient, 
        appID: int, 
        buyer: Account,
        amount: int, 
    ) -> None:
  
    appAddr = get_application_address(appID)
    appGlobalState = getAppGlobalState(client, appID)

    nftID = appGlobalState[b"nft_id"]
    seller_account =encoding.encode_address(appGlobalState[b"seller"])

    suggestedParams = client.suggested_params()

    payTxn = transaction.PaymentTxn(
        sender=buyer.getAddress(),
        receiver=appAddr,
        amt=amount,
        sp=suggestedParams,
    )

    appCallTxn = transaction.ApplicationDeleteTxn(
        sender=buyer.getAddress(),
        index=appID,
        foreign_assets=[nftID],
        app_args=[b"buy"],
        accounts=[seller_account],
        sp=suggestedParams,
    )

    transaction.assign_group_id([payTxn, appCallTxn])

    signedPayTxn = payTxn.sign(buyer.getPrivateKey())
    signedAppCallTxn = appCallTxn.sign(buyer.getPrivateKey())

    client.send_transactions([signedPayTxn, signedAppCallTxn])

    waitForTransaction(client, appCallTxn.get_txid())

    
def cancelSell(
        client: AlgodClient, 
        appID: int, 
        seller: Account,
    ):
    """Cancel an order.

    Args:
        client: An Algod client.
        appID: The app ID of the order.
        seller: The account initiating the close transaction. This must be
            either the seller or order creator if you wish to close the order
    """
    appGlobalState = getAppGlobalState(client, appID)
    nftID = appGlobalState[b"nft_id"]
    seller_account =encoding.encode_address(appGlobalState[b"seller"])

    suggestedParams = client.suggested_params()

    appCallTxn = transaction.ApplicationDeleteTxn(
        sender=seller.getAddress(),
        index=appID,
        app_args=[b"cancel"],
        foreign_assets=[nftID],
        accounts=[seller_account],
        sp=suggestedParams,
    )
   
    transaction.assign_group_id([appCallTxn])

    signedAppCallTxn = appCallTxn.sign(seller.getPrivateKey())

    client.send_transactions([signedAppCallTxn])

    waitForTransaction(client, appCallTxn.get_txid())
