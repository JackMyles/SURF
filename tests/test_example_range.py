import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def range_example() -> None:
    # Constants
    min_m_p = 0 # kW minimum motor power
    max_m_p = 80 # kW maximum motor power
    max_n_tr = 0.97 # maximum transmission efficiency
    min_n_tr = 0.95 # minimum transmission efficiency
    max_n_m = 0.92 # maximum motor efficiency
    min_n_m = 0.88 # minimum motor efficiency
    max_bat_e = 24 # kWh nominal battery energy
    min_bat_e = 0 # kWh minimum battery energy
    max_n_bat = 0.96 # maximum battery efficiency
    min_n_bat = 0.93 # minimum battery efficiency
    max_n_w = 0.99 # maximum wheel efficiency
    min_n_w = 0.97 # minimum wheel efficiency
    max_acc_e = 2 # kWh (should later be a function of temp)
    min_acc_e = 0.2 # kWH (should later be a function of temp)
    max_kwh_per_km = 0.125 # kWh per km (essentially worst fuel efficiency)
    min_kwh_per_km = 0.085 # kWh per km (essentially best fuel efficiency)

    # Contract for converting motor power to wheel power
    motor_wheel_power = PolyhedralContract.from_string(
        input_vars= ["p_m_out"],
        output_vars= ["p_w"],
        assumptions= [f"{min_m_p} <= p_m_out <= {max_m_p}"],
        guarantees= [f"{min_n_tr}p_m_out <= p_w <= {max_n_tr}p_m_out"]
    )

    # Contract for coverting motor power input to transmission power output
    motor_in_out_power = PolyhedralContract.from_string(
        input_vars= ["p_m_in"],
        output_vars= ["p_m_out"],
        assumptions= [f"{min_m_p} <= p_m_in <= {max_m_p}"],
        guarantees= [f"{min_n_m}p_m_in <= p_m_out <= {max_n_m}p_m_in"]
    )

    # Contract for converting battery power to motor power input
    battery_motor_power = PolyhedralContract.from_string(
        input_vars= ["p_bat", "p_acc"],
        output_vars= ["p_m_in"],
        assumptions= [f"{min_bat_e} <= p_bat <= {max_bat_e}", f"{min_acc_e} <= p_acc <= {max_acc_e}"],
        guarantees= [f"{min_n_bat}p_bat - p_acc <= p_m_in <= {max_n_bat}p_bat - p_acc"]
    )

    # Contract for converting transmission power to the final output power of the vehicle
    wheel_power_final = PolyhedralContract.from_string(
        input_vars= ["p_w"],
        output_vars= ["p_t"],
        assumptions= ["0 <= p_w"],
        guarantees= [f"{min_n_w}p_w <= p_t <= {max_n_w}p_w"]
    )

    # Contract for converting wheel power to the range of the vehicle
    power_range = PolyhedralContract.from_string(
        input_vars= ["p_t"],
        output_vars= ["r"],
        assumptions= ["0 <= p_t"],
        guarantees= [f"{1 / max_kwh_per_km}p_t <= r <= {1 / min_kwh_per_km}p_t"]
    )

    print("Battery to Motor Power Contract:")
    print(battery_motor_power)
    print("\nMotor to Transmission Power Contract:")
    print(motor_in_out_power)
    print("\nMotor to Wheel Power Contract:")
    print(motor_wheel_power)
    print("\nWheel Power to Final Power Contract:")
    print(wheel_power_final)
    print("\nFinal Power to Range Contract:")
    print(power_range)

    # Composition of the contracts
    contract_comp = battery_motor_power.compose(motor_in_out_power).compose(motor_wheel_power).compose(wheel_power_final).compose(power_range)
    print("\nComposition of Above Contracts")
    print(contract_comp)
    print(contract_comp.get_variable_bounds("r"))

range_example()
