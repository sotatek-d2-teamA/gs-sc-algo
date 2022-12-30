

from contract.nftContracts import approval_program, clear_state_program
from pyteal import compileTeal, Mode, Expr


def compileToTeal(contract: Expr) -> str:
    teal = compileTeal(contract, mode=Mode.Application, version=5)
    return teal


def compile():

    APPROVAL_PROGRAM = compileToTeal(approval_program())
    CLEAR_STATE_PROGRAM = compileToTeal(clear_state_program())

    print(APPROVAL_PROGRAM.replace('\n', '\\n'))
    print('\n')
    print(CLEAR_STATE_PROGRAM.replace('\n', '\\n'))



compile()
