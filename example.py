from time import time, sleep
from algosdk.mnemonic import *
from algosdk import account, encoding
from algosdk.logic import get_application_address
from auction.operations import createAuctionApp, mintAsset, withdrawAsset
from auction.util import (
    getBalances,
    getAppGlobalState,
    getLastBlockTimestamp,
)

from auction.testing.setup import getAlgodClient
from auction.testing.resources import (
    getTemporaryAccount,
    optInToAsset,
    createDummyAsset,
)
from auction.account import Account
from base64 import b64encode, b64decode


def simple_auction():
    client = getAlgodClient()

    admin = Account(to_private_key(
        'bonus fabric wise whale possible bunker ritual rhythm element stable sad deposit doll promote museum fun giggle peasant crash retreat beauty rigid gadget absorb rib')
    )
    # seller = Account(to_private_key(
    #     'bonus fabric wise whale possible bunker ritual rhythm element stable sad deposit doll promote museum fun giggle peasant crash retreat beauty rigid gadget absorb rib')
    # )
    user = Account(to_private_key(
        'harsh burst bacon inform arena before online cycle train survey blind depth stem crazy local blossom arrive census olympic grow miss subway clean abandon casual'))

    # bidder2 = Account(to_private_key(
    #     'wire friend element build awake offer obvious veteran silver dismiss shallow cheese nasty rule lock step wall dolphin baby artefact surprise cycle grunt about success'))

    # print("Alice (seller account):", admin.getAddress())
    # print("Bob (auction creator account):", user.getAddress())

    print("Create App")
    appID = createAuctionApp(
        client=client,
        sender=admin,

    )
    print(
        "Done. The app ID is",
        appID,
        "and the escrow account is",
        get_application_address(appID),
        "\n",
    )

    print("User call mint")
    mint = mintAsset(
        client=client,
        appID=appID,
        funder=user,

    )
    print(mint.logs[0])
    print(encoding.base64.b64decode(mint.logs[0]).decode('utf-8'))
    print(base64.b64decode(mint.logs[0]).decode('utf-8'))
    print(mint.logs[0].decode("utf-8"))
    print()

    print("Done\n")

    # print("User call withdraw")
    # mint = withdrawAsset(
    #     client=client,
    #     appID=appID,
    #     assetID=
    #     funder=user,

    # )
    # print(mint)
    # print("Done\n")


simple_auction()
