from time import sleep, time

from algosdk import account, encoding
from algosdk.logic import get_application_address
from algosdk.mnemonic import *

from test_helper.account import Account
from test_helper.operations import buyNft, cancelSell, createOrderApp, sellNFT
from test_helper.resources import (createDummyAsset, getTemporaryAccount,
                                   optInToAsset)
from test_helper.setup import getAlgodClient
from test_helper.util import getBalances, getAppGlobalState


def simple_auction():
    client = getAlgodClient()

    print("Generating temporary accounts...")
    seller = getTemporaryAccount(client)
    buyer = getTemporaryAccount(client)

    # seller = Account(to_private_key(
    #     'bonus fabric wise whale possible bunker ritual rhythm element stable sad deposit doll promote museum fun giggle peasant crash retreat beauty rigid gadget absorb rib')
    # )
    # buyer = Account(to_private_key(
    #     'harsh burst bacon inform arena before online cycle train survey blind depth stem crazy local blossom arrive census olympic grow miss subway clean abandon casual'))

    print("Alice (seller account):", seller.getAddress())
    print("Carla (buyer account)", buyer.getAddress(), "\n")

    print("Alice is generating an example NFT...")
    nftQuantity = 1
    nftID = createDummyAsset(client, nftQuantity, seller)
    print("The NFT ID is", nftID)
    print("Alice's balances:", getBalances(client, seller.getAddress()), "\n")

    nftPrice = 1_000_000  # 1 Algo
    print("Alice is creating an order to order off the NFT...")
    appID = createOrderApp(
        client=client,
        sender=seller,
        seller=seller.getAddress(),
        nftID=nftID,
        nftPrice=nftPrice,
        nftQuantity=nftQuantity,
    )
    actual = getAppGlobalState(client, appID)
    print("State when create")
    print(actual)
    print(
        "Done. The order app ID is",
        appID,
        "and the escrow account is",
        get_application_address(appID),
        "\n",
    )

    print("Alice is setting up and funding NFT order...")
    sellNFT(
        client=client,
        appID=appID,
        funder=seller,
        nftHolder=seller,
        nftID=nftID,
        nftQuantity=nftQuantity,
    )
    actual = getAppGlobalState(client, appID)
    print("State when sell asset")
    print(actual)
    sellerBalancesBefore = getBalances(client, seller.getAddress())
    sellerAlgosBefore = sellerBalancesBefore[0]
    print("Alice's balances:", sellerBalancesBefore)

    actualAppBalancesBefore = getBalances(client, get_application_address(appID))
    print("Order escrow balances:", actualAppBalancesBefore, "\n")

    buyerBalancesBefore = getBalances(client, buyer.getAddress())
    buyerAlgosBefore = buyerBalancesBefore[0]

    """
    # Cancel sell
    print("Alice cancel sell")
    cancelSell(client, appID, seller=seller)
    print("Done!")
    """

    print("Carla wants to buy on NFT, her balances:", buyerBalancesBefore)
    
    print("Carla is opting into NFT with ID", nftID)

    optInToAsset(client, nftID, buyer)
    
    print("Carla is placing buy for", nftPrice, "microAlgos")

    buyNft(client=client, appID=appID, buyer=buyer, amount=nftPrice)
    
    print("Done\n")

    print("Carla bought the NFT successful!\n")

    actualAppBalances = getBalances(client, get_application_address(appID))
    expectedAppBalances = {0: 0}
    print("The order escrow now holds the following:", actualAppBalances)
    assert actualAppBalances == expectedAppBalances

    buyerNftBalance = getBalances(client, buyer.getAddress())[nftID]
    assert buyerNftBalance == nftQuantity

    actualSellerBalances = getBalances(client, seller.getAddress())
    print("Alice's balances after order: ", actualSellerBalances, " Algos")
    actualBuyerBalances = getBalances(client, buyer.getAddress())
    print("Carla's balances after order: ", actualBuyerBalances, " Algos")


simple_auction()
