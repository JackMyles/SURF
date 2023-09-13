import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *

def lineFromPoints(P, Q, x, y) -> str:
 
    a = Q[1] - P[1]
    a = float("%f" % a)
    b = P[0] - Q[0]
    b = float("%f" % b)
    c = a*(P[0]) + b*(P[1])
    c = float("%f" % c)
 
    if(b < 0):
        return str(a) + f"{x} - " + str(-b) + f"{y} = " + str(c)
    else:
        return str(a) + f"{x} + " + str(b) + f"{y} = " + str(c)

def cost_range_example(min_bat, max_bat, min_m, max_m, min_tr, max_tr, max_budget) -> None:
    # Note the costs are all divided by 1000
    # Constants
    min_m_p = 0 # kW minimum motor power
    max_m_p = 80 # kW maximum motor power
    max_n_tr = max_tr[0] # maximum transmission efficiency
    min_n_tr = min_tr[0] # minimum transmission efficiency
    max_n_m = max_m[0] # maximum motor efficiency
    min_n_m = min_m[0] # minimum motor efficiency
    max_bat_e = 82 # kWh nominal battery energy
    min_bat_e = 0 # kWh minimum battery energy
    max_n_bat = max_bat[0] # maximum battery efficiency
    min_n_bat = min_bat[0] # minimum battery efficiency
    max_acc_e = 6 # kWh (should later be a function of temp)
    min_acc_e = 0.2 # kWh (should later be a function of temp)
    max_kwh_per_km = 0.267 # kWh per km (essentially worst fuel efficiency)
    min_kwh_per_km = 0.252 # kWh per km (essentially best fuel efficiency)
    min_degra = 0.0
    max_degra = 0.15

    # Battery Cost vs Efficiency
    cost_equation = lineFromPoints(min_bat, max_bat, "n_bat", "c_bat")
    battery = PolyhedralContract.from_string(
        input_vars= ["n_bat", "bat_e"],
        output_vars= ["c_bat"],
        assumptions= [f"{min_n_bat} <= n_bat <= {max_n_bat}", f"0 <= bat_e <= 85"],
        guarantees= ["0.138 bat_e + " + cost_equation]
    )

    # Motor Cost vs Efficiency
    cost_equation = lineFromPoints(min_m, max_m, "n_m", "c_m")
    motor = PolyhedralContract.from_string(
        input_vars= ["n_m"],
        output_vars= ["c_m"],
        assumptions= [f"{min_m[0]} <= n_m <= {max_m[0]}"],
        guarantees= [cost_equation]
    )

    # Transmission Cost vs Efficiency
    cost_equation = lineFromPoints(min_tr, max_tr, "n_tr", "c_tr")
    transmission = PolyhedralContract.from_string(
        input_vars= ["n_tr"],
        output_vars= ["c_tr"],
        assumptions= [f"{min_tr[0]} <= n_tr <= {max_tr[0]}"],
        guarantees= [cost_equation]
    )

    # Total Cost
    cost = PolyhedralContract.from_string(
        input_vars= ["c_bat", "c_m", "c_tr"],
        output_vars= ["t_c"],
        assumptions= [],
        guarantees= ["0.95 (c_bat + c_m + c_tr) <= t_c <= 1.05 (c_bat + c_m + c_tr)"]
    )

    # Contract for requirements
    requirements = PolyhedralContract.from_string(
        input_vars= [],
        output_vars= ["t_c"],
        assumptions= [],
        guarantees= [f"t_c <= {max_budget}"]
    )

    print("\nBattery Cost vs Efficiency Contract:")
    print(battery)
    print("\nMotor Cost vs Efficiency Contract:")
    print(motor)
    print("\nTransmission Cost vs Efficiency Contract:")
    print(transmission)

    # Composition of the contracts
    contract_comp = battery.merge(motor).merge(transmission).compose(cost)
    print("\nTotal Cost Contract:")
    print(contract_comp)

    # Merge requirements
    try:
        contract_merge = contract_comp.merge(requirements)
        print("\nRequirements Merged Contract:")
        print(contract_merge)
        print(contract_merge.get_variable_bounds("n_m"))
        print(contract_merge.get_variable_bounds("n_bat"))
        print(contract_merge.get_variable_bounds("n_tr"))
        print(contract_merge.get_variable_bounds("bat_e"))
        max_bat_e = contract_merge.get_variable_bounds("bat_e")[1]
        max_n_m = contract_merge.get_variable_bounds("n_m")[1]
        max_n_bat = contract_merge.get_variable_bounds("n_bat")[1]
        max_n_tr = contract_merge.get_variable_bounds("n_tr")[1]
    except:
        print("\nNo efficiencies exist within given budget")

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
        input_vars= ["p_bat", "p_acc", "p_cooling", "p_degra"],
        output_vars= ["p_m_in"],
        assumptions= [f"{min_bat_e} <= p_bat <= {max_bat_e}",
                      f"{min_acc_e} <= p_acc <= {max_acc_e}",
                      f"{1 - max_n_bat}p_bat <= p_cooling <= {1 - min_n_bat}p_bat",
                      f"{min_degra}p_bat <= p_degra <= {max_degra}p_bat"],
        guarantees= [f"{min_n_bat}p_bat - p_acc - p_cooling - p_degra <= p_m_in <= {max_n_bat}p_bat - p_acc - p_cooling - p_degra"]
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

    # Contract for range requirements (have not merged yet)
    requirements_range = PolyhedralContract.from_string(
        input_vars= [],
        output_vars= ["r"],
        assumptions= [],
        guarantees= ["r >= 130"]
    )

    # Composition of the contracts
    contract_comp1 = battery_motor_power.compose(motor_in_out_power).compose(motor_wheel_power).compose(wheel_power_range)
    print("\nComposition of Above Contracts")
    print(contract_comp1)

    contract_merge = contract_merge.merge(contract_comp1)
    print("\nRequirements Merged Contract:")
    print(contract_merge)
    print(contract_merge.get_variable_bounds("n_m"))
    print(contract_merge.get_variable_bounds("n_bat"))
    print(contract_merge.get_variable_bounds("n_tr"))
    print(contract_merge.get_variable_bounds("bat_e"))
    print(contract_merge.get_variable_bounds("t_c"))
    print(contract_merge.get_variable_bounds("r"))

min_bat = (0.88, 500)
max_bat = (0.95, 1000)
min_m = (0.90, 800)
max_m = (0.97, 1500)
min_tr = (0.93, 400)
max_tr = (0.98, 1200)
max_budget = 1700

cost_range_example(min_bat, max_bat, min_m, max_m, min_tr, max_tr, max_budget)
