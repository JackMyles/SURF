import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def cost_quotient_example() -> None:
    # Note the costs are all divided by 1000

    # Contract for converting motor power to wheel power
    battery = PolyhedralContract.from_string(
        input_vars= ["n_bat"],
        output_vars= ["c_bat"],
        assumptions= [f"{0.90} <= n_bat <= {0.97}"],
        guarantees= [f"c_bat = {500 / 7}n_bat - {415 / 7}"]
    )

    # Contract for coverting motor power input to transmission power output
    motor = PolyhedralContract.from_string(
        input_vars= ["n_m"],
        output_vars= ["c_m"],
        assumptions= [f"{0.88} <= n_m <= {0.95}"],
        guarantees= [f"c_m = {100}n_m - {80}"]
    )

    cost = PolyhedralContract.from_string(
        input_vars= ["c_bat", "c_m"],
        output_vars= ["t_c"],
        assumptions= [],
        guarantees= ["t_c = c_bat + c_m"]
    )

    print("Battery Cost vs Efficiency Contract:")
    print(battery)
    print("\nMotor Cost vs Efficiency Contract:")
    print(motor)

    # Composition of the contracts
    contract_comp = battery.merge(motor).compose(cost)
    print("\nComposition of Above Contracts")
    print(contract_comp)

cost_quotient_example()
