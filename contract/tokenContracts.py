from pyteal import *


def approval_program():
    # Global
    # asset_name = Bytes("asset_name")

    server_address = Bytes("server_address")
    admin_address = Bytes("admin_address")

    @Subroutine(TealType.none)
    def executeAssetCreationTxn() -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_name: Txn.application_args[1],
                TxnField.config_asset_unit_name: Txn.application_args[2],
                TxnField.config_asset_url: Txn.application_args[3],

                # 2**64 - 1
                # TODO: add option for amount to be fixed
                TxnField.config_asset_total: Int(9223372036854775806),

                # TODO: will be fixed later
                TxnField.config_asset_decimals: Int(6),
                TxnField.config_asset_manager: Global.current_application_address(),
                TxnField.config_asset_reserve: Global.current_application_address(),
                TxnField.config_asset_freeze: Global.current_application_address(),
                TxnField.config_asset_clawback: Global.current_application_address(),
            }),
            InnerTxnBuilder.Submit(),
            Log(Itob(InnerTxn.created_asset_id())),
        ])

    @Subroutine(TealType.none)
    def executeAssetTransferTxn() -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetTransfer,
                    TxnField.xfer_asset: Txn.assets[0],
                    TxnField.asset_receiver: Txn.accounts[1],
                    TxnField.asset_amount: Btoi(Txn.application_args[1]),
                }
            ),
            InnerTxnBuilder.Submit(),
            Log(Itob(Txn.assets[0])),
        ])

    on_create = Seq(
        # App.globalPut(asset_name, Txn.application_args[0]),
        App.globalPut(server_address, Txn.application_args[0]),
        App.globalPut(admin_address, Txn.application_args[1]),
        Approve(),
    )
    on_mint = Seq(  # only admin can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(admin_address)),
        Log(Txn.application_args[0]),  # mint
        executeAssetCreationTxn(),
        Log(Txn.accounts[1]),
        Approve(),
    )
    on_withdraw = Seq(  # only server can call
        Assert(Gtxn[Int(1)].sender() == App.globalGet(server_address)),
        Log(Txn.application_args[0]),  # withdraw
        executeAssetTransferTxn(),
        Log(Txn.accounts[1]),
        Log(Txn.application_args[1]),
        Approve(),
    )
    on_deposit = Seq(
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

    on_call_method = Txn.application_args[0]
    on_call = Cond(
        [on_call_method == Bytes("mint"), on_mint],
        [on_call_method == Bytes("withdraw"), on_withdraw],
        [on_call_method == Bytes("deposit"), on_deposit],

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
