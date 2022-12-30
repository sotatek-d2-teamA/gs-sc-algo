from pyteal import *


def approval_program():
    # Global
    asset_name = Bytes("asset_name")

    # @Subroutine(TealType.uint64)
    # def executeAssetCreationTxn(txn_index: TealType.uint64) -> TxnExpr:
    #     """
    #     returns the ID of the generated asset or fails
    #     """
    #     call_parameters = Gtxn[txn_index].application_args
    #     asset_total = Btoi(call_parameters[3])
    #     decimals = Btoi(call_parameters[4])
    #     return Seq([
    #         InnerTxnBuilder.Begin(),
    #         InnerTxnBuilder.SetFields({
    #             TxnField.type_enum: TxnType.AssetConfig,
    #             # TxnField.config_asset_name: call_parameters[1],
    #             # TxnField.config_asset_unit_name: call_parameters[2],
    #             # TxnField.config_asset_total: asset_total,
    #             # TxnField.config_asset_decimals: decimals,
    #             # TxnField.config_asset_url: call_parameters[5],

    #             # TxnField.config_asset_default_frozen: Int(1),
    #             # TxnField.config_asset_metadata_hash: call_parameters[0],

    #             TxnField.config_asset_manager: Global.current_application_address(),
    #             TxnField.config_asset_reserve: Global.current_application_address(),
    #             TxnField.config_asset_freeze: Global.current_application_address(),
    #             TxnField.config_asset_clawback: Global.current_application_address(),
    #         }),
    #         InnerTxnBuilder.Submit(),
    #         Log(Itob(InnerTxn.created_asset_id())),
    #         # InnerTxn.created_asset_id()
    #     ])

    @Subroutine(TealType.none)
    def executeAssetCreationTxn() -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields({
                TxnField.type_enum: TxnType.AssetConfig,
                TxnField.config_asset_name: App.globalGet(asset_name),
                TxnField.config_asset_unit_name: Txn.application_args[1],
                TxnField.config_asset_total: Int(1),
                TxnField.config_asset_decimals: Int(0),
                TxnField.config_asset_url: Txn.application_args[2],

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
                    # TxnField.asset_close_to:Txn.accounts[1],
                    TxnField.asset_amount: Int(1),
                }
            ),
            InnerTxnBuilder.Submit(),
        ])

    @Subroutine(TealType.none)
    def executeAssetDestroyTxn() -> TxnExpr:
        return Seq([
            InnerTxnBuilder.Begin(),
            InnerTxnBuilder.SetFields(
                {
                    TxnField.type_enum: TxnType.AssetConfig,
                    # TxnField.xfer_asset: Txn.assets[0],
                    TxnField.config_asset: Txn.assets[0]

                }
            ),
            InnerTxnBuilder.Submit(),
        ])

    on_create = Seq(
        App.globalPut(asset_name, Txn.application_args[0]),
        Approve(),
    )
    on_mint = Seq(
        executeAssetCreationTxn(),
        Approve(),
    )
    on_withdraw = Seq(
        executeAssetTransferTxn(),
        Approve(),
    )
    on_deposit = Seq(
        executeAssetDestroyTxn(),
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
