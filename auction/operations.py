from typing import Tuple, List

from algosdk.v2client.algod import AlgodClient
from algosdk.future import transaction
from algosdk.logic import get_application_address
from algosdk import account, encoding

from pyteal import compileTeal, Mode

from .account import Account
from .contracts import approval_program, clear_state_program
from .util import (
    PendingTxnResponse,
    waitForTransaction,
    fullyCompileContract,
    getAppGlobalState,
)

APPROVAL_PROGRAM = b""
CLEAR_STATE_PROGRAM = b""


def getContracts(client: AlgodClient) -> Tuple[bytes, bytes]:
    global APPROVAL_PROGRAM
    global CLEAR_STATE_PROGRAM

    if len(APPROVAL_PROGRAM) == 0:
        APPROVAL_PROGRAM = fullyCompileContract(client, approval_program())
        CLEAR_STATE_PROGRAM = fullyCompileContract(
            client, clear_state_program())

    return APPROVAL_PROGRAM, CLEAR_STATE_PROGRAM


def createAuctionApp(
    client: AlgodClient,
    sender: Account,
) -> int:

    approval, clear = getContracts(client)

    globalSchema = transaction.StateSchema(num_uints=7, num_byte_slices=2)
    localSchema = transaction.StateSchema(num_uints=0, num_byte_slices=0)

    app_args = [
        b"Character"
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


def mintAsset(
    client: AlgodClient,
    appID: int,
    funder: Account,
) -> PendingTxnResponse:

    appAddr = get_application_address(appID)

    suggestedParams = client.suggested_params()

    fundingAmount = (
        350_000
    )

    app_args = [
        b"mint",
    ]

    fundAppTxn = transaction.PaymentTxn(
        sender=funder.getAddress(),
        receiver=appAddr,
        amt=fundingAmount,
        sp=suggestedParams,
    )

    setupTxn = transaction.ApplicationCallTxn(
        sender=funder.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=app_args,

        accounts=[funder.getAddress()],
        # foreign_assets=[nftID],

        sp=suggestedParams,
    )

    transaction.assign_group_id([fundAppTxn, setupTxn])

    signedFundAppTxn = fundAppTxn.sign(funder.getPrivateKey())
    signedSetupTxn = setupTxn.sign(funder.getPrivateKey())

    client.send_transactions(
        [signedFundAppTxn, signedSetupTxn])

    response = waitForTransaction(client, signedSetupTxn.get_txid())
    


    return response


def withdrawAsset(
    client: AlgodClient,
    appID: int,
    assetID: int,
    funder: Account,

) -> None:
    suggestedParams = client.suggested_params()

    app_args = [
        b"withdraw",
    ]

    # opt in
    optInTxn = transaction.AssetTransferTxn(
        sender=funder.getAddress(),
        index=assetID,
        sp=suggestedParams,
    )

    # withdraw
    withdrawTxn = transaction.ApplicationCallTxn(
        sender=funder.getAddress(),
        index=appID,
        on_complete=transaction.OnComplete.NoOpOC,
        app_args=app_args,

        accounts=[funder.getAddress()],
        foreign_assets=[assetID],

        sp=suggestedParams,
    )

    transaction.assign_group_id([optInTxn, withdrawTxn])

    signedOptInTxn = optInTxn.sign(funder.getPrivateKey())
    signedWithdrawTxn = withdrawTxn.sign(funder.getPrivateKey())

    client.send_transactions(
        [signedOptInTxn, signedWithdrawTxn])

    response = waitForTransaction(client, signedWithdrawTxn.get_txid())
    return response
