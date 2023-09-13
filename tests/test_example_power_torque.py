import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def power_to_torque_example() -> None:
    # Constants
    rpm = 1000
    c1 = 1000 * 9.549 / rpm
    i_x = 4.171 # first gear
    i_0 = 3.460 # final drive
    n_w = 2 # number of driving wheels
    c2 = i_x * i_0 / n_w

    # Contract for converting power to engine torque
    contract1 = PolyhedralContract.from_string(
        input_vars= ["p"],
        output_vars= ["t_e"],
        assumptions= ["0 <= p <= 100"],
        guarantees= [f"t_e = {c1}p"],
    )

    # Contract for coverting engine torque to wheel torque
    contract2 = PolyhedralContract.from_string(
        input_vars= ["t_e"],
        output_vars= ["t_w"],
        assumptions= ["t_e >= 0"],
        guarantees= [f"t_w = {c2}t_e"],
    )
    print("Power to Engine Torque Contract:")
    print(contract1)
    print("\nPower to Wheel Torque Contract:")
    print(contract2)

    # Composition of the two contracts
    contract_comp = contract1.compose(contract2)
    print("\nComposition of Above Contracts")
    print(contract_comp)

power_to_torque_example()
