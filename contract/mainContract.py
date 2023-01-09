from pyteal import *


def approval_program():
    # Global
    server_address = Bytes("server_address")
    admin_address = Bytes("admin_address")

#########################################################################################
    @Subroutine(TealType.none)
    def executeAssetCreationTxn(totalAmount: Expr, decimals: Expr) -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_name: Txn.application_args[1],
                TxnField.config_asset_unit_name: Txn.application_args[2],
                TxnField.config_asset_url: Txn.application_args[3],

                TxnField.config_asset_total: totalAmount,
                TxnField.config_asset_decimals: decimals,

                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }),
            InnerTxnBuilder.Submit(),
            Log(Itob(InnerTxn.created_asset_id())),
        ])

    @Subroutine(TealType.none)
    def executeAssetTransferTxn(amount: Expr) -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: Txn.assets[0],
                    TxnField.asset_receiver: Txn.accounts[1],
                    TxnField.asset_amount: amount,
                }
            ),
            InnerTxnBuilder.Submit(),
            Log(Itob(Txn.assets[0])),
        ])

    @Subroutine(TealType.none)
    def executeAssetDestroyTxn() -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetConfig,
                    TxnField.config_asset: Txn.assets[0]
                }
            ),
            InnerTxnBuilder.Submit(),
            Log(Itob(Txn.assets[0])),
        ])
        
#########################################################################################

    on_create = Seq(
        App.globalPut(server_address, Txn.application_args[0]),
        App.globalPut(admin_address, Txn.application_args[1]),
        Approve(),
    )
#########################################################################################
    # Token

    on_mint_token = Seq(  # only admin can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(admin_address)),
        Log(Txn.application_args[0]),  # mint
        executeAssetCreationTxn(Int(9223372036854775806), Int(6)),
        Log(Txn.accounts[1]),
        Approve(),
    )

    on_withdraw_token = Seq(  # only server can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # withdraw
        executeAssetTransferTxn(Btoi(Txn.application_args[1])),
        Log(Txn.accounts[1]),
        Log(Txn.application_args[1]),
        Approve(),
    )

    on_deposit_token = Seq(
        Assert(Gtxn[Int(0)].asset_amount() == Btoi(Txn.application_args[1])),
        Assert(Gtxn[Int(0)].xfer_asset() == Txn.assets[0]),
        Assert(Gtxn[Int(0)].sender() == Txn.sender()),
        Assert(Gtxn[Int(0)].asset_receiver(
        ) == Global.current_application_address()),

        Log(Txn.application_args[0]),  # deposit
        Log(Itob(Txn.assets[0])),
        Log(Txn.accounts[1]),
        Log(Txn.application_args[1]),
        Approve(),
    )

#########################################################################################
    # NFT

    on_mint_nft = Seq(
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # mint
        executeAssetCreationTxn(Int(1), Int(0)),
        Log(Txn.accounts[1]),
        Approve(),
    )

    on_withdraw_nft = Seq(
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # withdraw
        executeAssetTransferTxn(Int(1)),
        Log(Txn.accounts[1]),
        Approve(),
    )

    on_deposit_nft = Seq(
        # check if user is send enough
        Assert(Gtxn[Int(0)].asset_amount() == Int(1)),
        Assert(Gtxn[Int(0)].xfer_asset() == Txn.assets[0]),
        Assert(Gtxn[Int(0)].sender() == Txn.sender()),
        Assert(Gtxn[Int(0)].asset_receiver(
        ) == Global.current_application_address()),

        Log(Txn.application_args[0]),  # deposit
        executeAssetDestroyTxn(),
        Log(Txn.accounts[1]),
        Approve(),
    )

#########################################################################################
    # Item

    on_mint_item = Seq(  # only server can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # mint
        executeAssetCreationTxn(Int(9223372036854775806), Int(0)),
        Log(Txn.accounts[1]),
        Approve(),
    )

    on_withdraw_item = Seq(
        # only server can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # withdraw
        executeAssetTransferTxn(Btoi(Txn.application_args[1])),
        Log(Txn.accounts[1]),
        Log(Txn.application_args[1]),
        Approve(),
    )

    on_deposit_item = Seq(
        Assert(Gtxn[Int(0)].asset_amount() == Btoi(Txn.application_args[1])),
        Assert(Gtxn[Int(0)].xfer_asset() == Txn.assets[0]),
        Assert(Gtxn[Int(0)].sender() == Txn.sender()),
        Assert(Gtxn[Int(0)].asset_receiver(
        ) == Global.current_application_address()),

        Log(Txn.application_args[0]),  # deposit
        Log(Itob(Txn.assets[0])),
        Log(Txn.accounts[1]),
        Log(Txn.application_args[1]),
        Approve(),
    )

#########################################################################################

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        # Token
        [on_call_method == Bytes("mint_token"), on_mint_token],
        [on_call_method == Bytes("withdraw_token"), on_withdraw_token],
        [on_call_method == Bytes("deposit_token"), on_deposit_token],

        # NFT
        [on_call_method == Bytes("mint_nft"), on_mint_nft],
        [on_call_method == Bytes("withdraw_nft"), on_withdraw_nft],
        [on_call_method == Bytes("deposit_nft"), on_deposit_nft],

        # Item
        [on_call_method == Bytes("mint_item"), on_mint_item],
        [on_call_method == Bytes("withdraw_item"), on_withdraw_item],
        [on_call_method == Bytes("deposit_item"), on_deposit_item],
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.NoOp, on_call],
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

#########################################################################################


def clear_state_program():
    return Approve()


with open("teal/nft/auction_approval.teal", "w") as f:
    compiled = compileTeal(
        approval_program(), mode=Mode.Application, version=5)
    f.write(compiled)

with open("teal/nft/auction_clear_state.teal", "w") as f:
    compiled = compileTeal(clear_state_program(),
                           mode=Mode.Application, version=5)
    f.write(compiled)
