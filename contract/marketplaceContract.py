from pyteal import *


def approval_program():
    seller = Bytes("seller")
    nft_id = Bytes("nft_id")
    nft_price = Bytes("nft_price")
    nft_quantity = Bytes("nft_quantity")
    nft_status = Bytes("nft_status")

    @Subroutine(TealType.none)
    def closeNFTTo(assetID: Expr) -> Expr:
        asset_holding = AssetHolding.balance(
            Global.current_application_address(), assetID
        )
        return Seq(
            asset_holding,
            If(asset_holding.hasValue()).Then(
                Seq(
                    InnerTxnBuilder.Begin(),
                    InnerTxnBuilder.SetFields(
                        {
                            TxnField.type_enum: TxnType.AssetTransfer,
                            TxnField.xfer_asset: assetID,
                            TxnField.asset_close_to: Txn.sender(),
                        }
                    ),
                    InnerTxnBuilder.Submit(),
                )
            ),
        )

    @Subroutine(TealType.none)
    def closeAccountTo(account: Expr) -> Expr:
        return If(Balance(Global.current_application_address()) != Int(0)).Then(
            Seq(
                InnerTxnBuilder.Begin(),
                InnerTxnBuilder.SetFields(
                    {
                        TxnField.type_enum: TxnType.Payment,
                        TxnField.close_remainder_to: account,
                    }
                ),
                InnerTxnBuilder.Submit(),
            )
        )

    on_create = Seq(
        App.globalPut(seller, Txn.application_args[0]),
        App.globalPut(nft_id, Btoi(Txn.application_args[1])),
        App.globalPut(nft_price, Btoi(Txn.application_args[2])),
        App.globalPut(nft_quantity, Btoi(Txn.application_args[3])),
        Assert(App.globalGet(nft_quantity) > Int(0)),
        App.globalPut(nft_status, Bytes("on_create")),  
        Approve(),
    )

    on_sell = Seq( 
        # TODO:
        # assert quantity,nft_id, seller from transfer asset
        # assert amount algo from algo payment transaction
        
        Assert(App.globalGet(nft_status) != Bytes("on_sell")),

        # opt into NFT asset -- because you can't opt in if you're already opted in, this is what
        # we'll use to make sure the contract has been set up
        InnerTxnBuilder.Begin(),
        InnerTxnBuilder.SetFields(
            {
                TxnField.type_enum: TxnType.AssetTransfer,
                TxnField.xfer_asset: App.globalGet(nft_id),
                TxnField.asset_receiver: Global.current_application_address(),
            }
        ),
        InnerTxnBuilder.Submit(),   
        App.globalPut(nft_status, Bytes("on_sell")),
        Approve(),
    )

    on_buy_txn_index = Txn.group_index() - Int(1)
    on_buy_nft_holding = AssetHolding.balance(
        Global.current_application_address(), App.globalGet(nft_id)
    )
    on_buy = Seq(
        on_buy_nft_holding,
        Assert(
            And(
                # the order has been set up
                on_buy_nft_holding.hasValue(),
                on_buy_nft_holding.value() > Int(0),
                on_buy_nft_holding.value() == App.globalGet(nft_quantity),
                # the actual bid payment is before the app call
                Gtxn[on_buy_txn_index].type_enum() == TxnType.Payment,
                Gtxn[on_buy_txn_index].sender() == Txn.sender(),
                Gtxn[on_buy_txn_index].receiver()
                == Global.current_application_address(),
                Gtxn[on_buy_txn_index].amount() >= App.globalGet(nft_price),
            )
        ),
        closeNFTTo(App.globalGet(nft_id)),
        # send remaining funds to the seller
        closeAccountTo(App.globalGet(seller)),
        Log(Bytes("on_buy")),
        Approve(),
    )

    on_cancel = Seq(
        Assert(
            Or(
                # sender must either be the seller or the order creator
                Txn.sender() == App.globalGet(seller),
                Txn.sender() == Global.creator_address(),
            )
        ),
        closeNFTTo(App.globalGet(nft_id)),
        closeAccountTo(App.globalGet(seller)),
        Log(Bytes("on_cancel")),
        Approve()
    )

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("sell"), on_sell],
    )

    on_call_delete = Cond(
        [on_call_method == Bytes("buy"), on_buy],
        [on_call_method == Bytes("cancel"), on_cancel],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
        [
            Txn.on_completion() == OnComplete.DeleteApplication,
            on_call_delete,
        ],
        [
            Or(
                Txn.on_completion() == OnComplete.OptIn,
                Txn.on_completion() == OnComplete.CloseOut,
                Txn.on_completion() == OnComplete.UpdateApplication,
            ),
            Reject(),
        ],
    )
    return program

def clear_state_program():
    return Approve()

with open("teal/marketplace/auction_approval.teal", "w") as f:
    compiled = compileTeal(approval_program(), mode=Mode.Application, version=5)
    f.write(compiled)

with open("teal/marketplace/auction_clear_state.teal", "w") as f:
    compiled = compileTeal(clear_state_program(), mode=Mode.Application, version=5)
    f.write(compiled)
