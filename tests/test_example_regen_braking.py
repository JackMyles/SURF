import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *


def regen_braking_example() -> None:
    # Constants
    m_i = 0 # m_c * (0.04 + 0.0025 * G^2) fictitious mass taking into account inertia of rotating components
    r_r = 1 # u_rr * m_v * g * cos(c) # rolling resistance
    a_d = 1 # 0.5 * p * A * C_d * v_t^2 # aerodynamic drag
    g_r = 1 # m_v * g * sin(c) # grading resistance
    l_a = 1 # (m_v + m_i) * a_t # linear acceleration
    max_v_t = 140 # kmph max velocity
    max_m_p = 80 # kW max motor power
    n_tr = 0.97 # transmission efficiency
    n_rb = 0.90 # regenerative braking efficiency (e^(0.0411/a_t))^-1
    n_m = 0.90 # motor efficiency
    max_bat_e = 24 # kWh nominal battery energy
    min_bat_e = 0 # kWh minimum battery energy
    n_bat = 0.95 # battery efficiency
    max_acc_e = 6 # kWh (should later be a function of temp)
    min_acc_e = 0.2 # kWH (should later be a function of temp)
    kwh_per_km = 0.115 # kWh per km (essentially fuel efficiency)

    # Contract for converting velocity to wheel power
    velocity_wheel_power = PolyhedralContract.from_string(
        input_vars= ["v_t"],
        output_vars= ["p_w"],
        assumptions= [f"0 <= v_t <= {max_v_t}"],
        # coefficients may need to be functions
        guarantees= [f"p_w = {-(r_r + a_d + g_r + l_a)}v_t"]
    )

    # Contract for converting wheel power to motor power
    wheel_motor_power = PolyhedralContract.from_string(
        input_vars= ["p_w"],
        output_vars= ["p_m_out"],
        assumptions= [f"{-max_m_p} <= p_w <= 0"],
        guarantees= [f"p_m_out = {n_tr * n_rb}p_w"]
    )

    # Contract for coverting transmission power to generator power
    motor_out_in_power = PolyhedralContract.from_string(
        input_vars= ["p_m_out"],
        output_vars= ["p_m_in"],
        assumptions= [f"{-max_m_p} <= p_m_out <= {0}"],
        guarantees= [f"p_m_in = {n_m}p_m_out"]
    )

    # Contract for coverting power generated to battery power
    motor_battery_power = PolyhedralContract.from_string(
        input_vars= ["p_m_in"],
        output_vars= ["p_bat"],
        assumptions= ["p_m_in <= 0"],
        guarantees= [f"p_bat = {n_bat}p_m_in"]
    )

    print("Velocity to Wheel Power Contract:")
    print(velocity_wheel_power)
    print("\nWheel to Motor Power Contract:")
    print(wheel_motor_power)
    print("\Transmission to Generator Power Contract:")
    print(motor_out_in_power)
    print("\nGenerator Power to Battery Power Contract:")
    print(motor_battery_power)

    # Composition of the contracts
    contract_comp = velocity_wheel_power.compose(wheel_motor_power).compose(motor_out_in_power).compose(motor_battery_power)
    print("\nComposition of Above Contracts")
    print(contract_comp)

regen_braking_example()
