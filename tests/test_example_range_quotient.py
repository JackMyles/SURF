import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def range_quotient_example() -> None:
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
    max_acc_e = 6 # kWh (should later be a function of temp)
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

    # Contract for converting wheel power to the range of the vehicle
    wheel_power_range = PolyhedralContract.from_string(
        input_vars= ["p_w"],
        output_vars= ["r"],
        assumptions= ["0 <= p_w"],
        guarantees= [f"{1 / max_kwh_per_km}p_w <= r <= {1 / min_kwh_per_km}p_w"]
    )

    print("Battery to Motor Power Contract:")
    print(battery_motor_power)
    print("\nMotor to Transmission Power Contract:")
    print(motor_in_out_power)
    print("\nMotor to Wheel Power Contract:")
    print(motor_wheel_power)
    print("\nWheel Power to Range Contract:")
    print(wheel_power_range)

    # Composition of the contracts
    contract_comp = motor_in_out_power.compose(motor_wheel_power).compose(wheel_power_range)

    # Quotient to find needed efficiency of non-battery components
    contract_top_level = PolyhedralContract.from_string(
        input_vars= ["p_bat", "p_acc"],
        output_vars= ["r"],
        assumptions= ["0 <= p_bat <= 24", "0.2 <= p_acc <= 6"],
        guarantees= ["-6.688 p_acc + 6.22 p_bat - r <= 0", "10.5 p_acc - 10.08 p_bat + r <= 0"]
    )
    print("\nQuotient for Efficiency of Non-battery Components")
    contract_missing_subsystem_1 = contract_top_level.quotient(contract_comp)
    #contract_missing_subsystem_2 = contract_missing_subsystem_1.quotient(wheel_power_range)
    print(contract_missing_subsystem_1)

range_quotient_example()
