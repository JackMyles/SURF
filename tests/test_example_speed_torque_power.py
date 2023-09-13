import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def speed_to_torque_and_power_example() -> None:
    # Contract for converting engine rpm to engine torque
    torque_contract1 = PolyhedralContract.from_string(
        input_vars= ["s"],
        output_vars= ["t"],
        assumptions= ["0 <= s <= 1300"],
        guarantees= ["600 <= t <= 800"]
    )

    # Contract for converting engine rpm to engine torque
    torque_contract2 = PolyhedralContract.from_string(
        input_vars= ["s"],
        output_vars= ["t"],
        assumptions= ["1300 <= s <= 5000"],
        guarantees= ["-0.1081s + 740.5405 <= t <= -0.1621s + 1010.8108"]
    )

    # Contract for coverting power to engine rpm
    speed_contract1 = PolyhedralContract.from_string(
        input_vars= ["p"],
        output_vars= ["s"],
        assumptions= ["0 <= p <= 100"],
        guarantees= ["10p <= s <= 17p"]
    )

    # Contract for converting power to engine rpm
    speed_contract2 = PolyhedralContract.from_string(
        input_vars= ["p"],
        output_vars= ["s"],
        assumptions= ["100 <= p <= 130"],
        guarantees= ["1700 <= s <= -110p + 16000"]
    )
    print("\nEngine Power to Engine Speed Contract 1:")
    print(speed_contract2)
    print("\nEngine Power to Engine Speed Contract 2:")
    print(speed_contract2)
    print("\nEngine Speed to Engine Torque Contract 1:")
    print(torque_contract1)
    print("\nEngine Speed to Engine Torque Contract 2:")
    print(torque_contract2)

    # Composition of the first of each contract
    contract_comp1 = speed_contract1.compose(torque_contract1)
    print("\nComposition of First Speed and Torque Contracts")
    print(contract_comp1)

    # Composition of the second of each contract
    contract_comp2 = speed_contract2.compose(torque_contract2)
    print("\nComposition of Second Speed and Torque Contracts")
    print(contract_comp2)
    
speed_to_torque_and_power_example()
