import pacti.iocontract as iocontract
from pacti.terms.polyhedra import *
from typing import Optional, List, Tuple, Dict, Union
# from IPython import display
from pacti import write_contracts_to_file
from pacti.iocontract import Var
import operator
from dataclasses import dataclass
import numpy as np
import pathlib
from pacti.terms.polyhedra.plots import plot_guarantees
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backend_bases import Event
from matplotlib.axes import Axes
numeric = Union[int, float]

def scenario_sequence(
    c1: PolyhedralContract,
    c2: PolyhedralContract,
    variables: list[str],
    c1index: int,
    c2index: Optional[int] = None,
    file_name: Optional[str] = None,
) -> PolyhedralContract:
    """
    Composes c1 with a c2 modified to rename its entry variables according to c1's exit variables

    Args:
        c1: preceding step in the scenario sequence
        c2: next step in the scenario sequence
        variables: list of entry/exit variable names for renaming
        c1index: the step number for c1's variable names
        c2index: the step number for c2's variable names; defaults ti c1index+1 if unspecified

    Returns:
        c1 composed with a c2 modified to rename its c2index-entry variables
        to c1index-exit variables according to the variable name correspondences
        with a post-composition renaming of c1's exit variables to fresh outputs
        according to the variable names.
    """
    if not c2index:
        c2index = c1index + 1
    c2_inputs_to_c1_outputs = [(f"{v}{c2index}_initial", f"{v}{c1index}_final") for v in variables]
    keep_c1_outputs = [f"{v}{c1index}_final" for v in variables]
    renamed_c1_outputs = [(f"{v}{c1index}_final", f"output_{v}{c1index}") for v in variables]

    c2_with_inputs_renamed = c2.rename_variables(c2_inputs_to_c1_outputs)
    c12_with_outputs_kept = c1.compose(c2_with_inputs_renamed, vars_to_keep=keep_c1_outputs)
    c12 = c12_with_outputs_kept.rename_variables(renamed_c1_outputs)

    if file_name:
        write_contracts_to_file(
            contracts=[c1, c2_with_inputs_renamed, c12_with_outputs_kept],
            names=["c1", "c2_with_inputs_renamed", "c12_with_outputs_kept"],
            file_name=file_name,
        )

    return c12

def bounds(c: PolyhedralContract) -> List[str]:
    bounds=[]
    for v in sorted(c.inputvars, key=operator.attrgetter('name')):
        low, high = bound(c, v.name)
        bounds.append(f" input {v.name} in [{low},{high}]")

    for v in sorted(c.outputvars, key=operator.attrgetter('name')):
        low, high = bound(c, v.name)
        bounds.append(f"output {v.name} in [{low},{high}]")

    return bounds

def bound(c: PolyhedralContract, var: str) -> Tuple[str, str]:
    try:
        b = c.get_variable_bounds(var)
        if isinstance(b[0], float):
            low = f"{b[0]:.2f}"
        else:
            low = "None"
        if isinstance(b[1], float):
            high = f"{b[1]:.2f}"
        else:
            high = "None"
        return low, high
    except ValueError:
        return "unknown", "unknown"

# Parameters:
# - s: index of the timeline variables
# - generation: (min, max) rate of battery charge during the task instance
def charge_power(s: int, generation: Tuple[float, float]) -> PolyhedralContract:
    spec = PolyhedralContract.from_string(
        input_vars = [
            f"soc{s}_initial",         # initial battery SOC
            f"duration_charging{s}"    # variable task duration
        ],
        output_vars = [
            f"soc{s}_final"            # final battery SOC
        ],
        assumptions = [
            f"0 <= duration_charging{s}",
            f"0 <= soc{s}_initial <= 100.0",
            f"soc{s}_initial + {generation[1]}*duration_charging{s} <= 100"
        ],
        guarantees = [
            f"{generation[0]}*duration_charging{s} <= soc{s}_final - soc{s}_initial <= {generation[1]}*duration_charging{s}",
            f"soc{s}_final <= 100.0",
            f"0 <= soc{s}_final"
        ]
    )
    return spec

# Parameters:
# - s: start index of the timeline variables
# - consumption: (min, max) rate of battery discharge during the task instance
def power_consumer(s: int, task: str, consumption: Tuple[float, float]) -> PolyhedralContract:
  spec = PolyhedralContract.from_string(
        input_vars = [
            f"soc{s}_initial",       # initial battery SOC
            f"distance_{task}{s}"    # variable task distance
            ],
            output_vars = [
            f"soc{s}_final"          # final battery SOC
        ],
        assumptions = [
            # Task has a positive scheduled distance
            f"0 <= distance_{task}{s}",
            # Upper bound on initial soc
            f"soc{s}_initial <= 100.0",
            # Lower bound on initial soc
            f"0 <= soc{s}_initial",
            # Battery has enough energy for worst-case consumption throughout the task instance
            f"soc{s}_initial >= {consumption[1]}*distance_{task}{s}"
        ],
        guarantees=[
            # distance*consumption(min) <= soc{initial} - soc{final} <= distance*consumption(max)
            f"{consumption[0]}*distance_{task}{s} <= soc{s}_initial - soc{s}_final <= {consumption[1]}*distance_{task}{s}",
            # Battery cannot exceed maximum SOC
            f"soc{s}_final <= 100",
            # Battery should not completely discharge
            f"0 <= soc{s}_final"
        ]
  )
  return spec

def get_bounds(ptl: PolyhedralTermList, var: str) -> tuple[str, str]:
    try:
        min = f"{ptl.optimize(objective={Var(var): 1}, maximize=False):.2f}"
    except ValueError:
        min = "unknown"
    try:
        max = f"{ptl.optimize(objective={Var(var): 1}, maximize=True):.2f}"
    except ValueError:
        max = "unknown"

    return min, max 

def calculate_output_bounds_for_input_value(ptl: PolyhedralTermList, inputs: Dict[Var, float], output: Var) -> tuple[str,str]:
    return get_bounds(ptl.evaluate(inputs).simplify(), output.name)

def consumption_calc(incline: int, d_type: str, fuel_eco: Tuple[float, float], mileage: int, temp: int) -> Tuple[float, float]:
    # Incline keys in grade value
    # power_avgs_incline = {"-5" : 0.09, "-4" : 0.13, "-3" : 0.25, "-2" : 0.45, "-1" : 0.75, "0" : 1, "1" : 1.21, "2" : 1.5, "3" : 1.76, "4" : 2.00, "5" : 2.34}
    if incline == 0:
        power_avgs_incline = 1.0
    elif incline >= -3 and incline < 0:
        power_avgs_incline = 0.25 * incline + 1
    elif incline > 0:
        power_avgs_incline = 0.268 * incline + 1
    else:
        power_avgs_incline = 0.1

    power_avgs_type = {"hwy" : 1.09, "cty" : 1}

    # Temp in degrees celsius
    power_avgs_temp = 1.00
    if temp <= 10:
        power_avgs_temp = 2 - (0.017 * temp + 0.84)
    elif temp > 30:
        power_avgs_temp = 2 - (-0.025 * temp + 1.8)

    if mileage <= 25000:
        power_avgs_mileage = 0.000002 * mileage + 1
    elif mileage > 25000:
        power_avgs_mileage = 0.0000004 * mileage + 1.05

    consumption = [i * power_avgs_type[d_type] * power_avgs_incline * power_avgs_mileage * power_avgs_temp for i in fuel_eco]
    return tuple(consumption)

def on_hover(ptl: PolyhedralTermList, x_var: Var, y_var: Var, fig: Figure, ax: Axes, event: Event) -> None:
    if event.inaxes == ax:
        x_coord = event.xdata
        try:
            y_min, y_max = calculate_output_bounds_for_input_value(ptl, {x_var: x_coord}, y_var)
            ax.set_title(f"@ {x_var.name}={x_coord:.2f}\n{y_min} <= {y_var.name} <= {y_max}")
        except ValueError as e:
            print(f"Contract guarantee hover ValueError:\n{e}")
            ax.set_title(f"@ {x_var.name}={x_coord:.2f}\nValueError (see message below)")
        fig.canvas.draw_idle()

def plot_guarantees_with_bounds_hover(
    contract: PolyhedralContract,
    x_var: Var,
    y_var: Var,
    var_values: Dict[Var, numeric],
    x_lims: Tuple[numeric, numeric],
    y_lims: Tuple[numeric, numeric],
) -> Figure:
    fig: Figure = plot_guarantees(contract=contract, x_var=x_var, y_var=y_var, var_values=var_values, x_lims=x_lims, y_lims=y_lims)
    constraints: PolyhedralTermList = contract.a | contract.g
    fig.canvas.mpl_connect('button_press_event', lambda event: on_hover(constraints.evaluate(var_values).simplify(), x_var, y_var, fig, fig.axes[0], event))
    return fig

charging1_power = charge_power(s=1, generation=(3.33, 4.55))
print(f"Contract charging1_power:\n\n{charging1_power}")

graph1 = plot_guarantees_with_bounds_hover(contract=charging1_power,
                x_var=Var("duration_charging1"),
                y_var=Var("soc1_final"),
                var_values={
                  Var("soc1_initial"):0,
                },
                x_lims=(0,30),
                y_lims=(0,100))

charging2_power = charge_power(s=2, generation=(0.21, 0.24))
print(f"Contract charging2_power:\n\n{charging2_power}")

graph2 = plot_guarantees_with_bounds_hover(contract=charging2_power,
                x_var=Var("duration_charging2"),
                y_var=Var("soc2_final"),
                var_values={
                  Var("soc2_initial"):0,
                },
                x_lims=(0,500),
                y_lims=(0,100))

# Fuel Economy for Tesla Model 3 (82 kWh battery, 0.252 to 0.255 kWh per mile, ~0.30 to 0.32 % charge per mile) in charge lost per mile
cty1_power = power_consumer(s=1, task="cty", consumption=consumption_calc(0, "cty", [0.30, 0.32], 0, 20))
print(f"Contract cty1_power:\n\n{cty1_power}")

graph3 = plot_guarantees_with_bounds_hover(contract=cty1_power,
                x_var=Var("distance_cty1"),
                y_var=Var("soc1_final"),
                var_values={
                  Var("soc1_initial"):100,
                },
                x_lims=(0,400),
                y_lims=(0,100))


cty4_power = power_consumer(s=4, task="cty", consumption=consumption_calc(0, "cty", [0.30, 0.32], 200000, 20))
print(f"Contract cty4_power:\n\n{cty4_power}")

graph4 = plot_guarantees_with_bounds_hover(contract=cty4_power,
                x_var=Var("distance_cty4"),
                y_var=Var("soc4_final"),
                var_values={
                  Var("soc4_initial"):100,
                },
                x_lims=(0,400),
                y_lims=(0,100))

hwy5_power = power_consumer(s=5, task="hwy", consumption=consumption_calc(-1, "hwy", [0.30, 0.32], 30000, 20))
print(f"Contract hwy5_power:\n\n{hwy5_power}")

graph5 = plot_guarantees_with_bounds_hover(contract=hwy5_power,
                x_var=Var("distance_hwy5"),
                y_var=Var("soc5_final"),
                var_values={
                  Var("soc5_initial"):100,
                },
                x_lims=(0,400),
                y_lims=(0,100))

hwy6_power = power_consumer(s=6, task="hwy", consumption=consumption_calc(2, "cty", [0.30, 0.32], 30000, 0))
print(f"Contract hwy6_power:\n\n{hwy6_power}")

graph6 = plot_guarantees_with_bounds_hover(contract=hwy6_power,
                x_var=Var("distance_hwy6"),
                y_var=Var("soc6_final"),
                var_values={
                  Var("soc6_initial"):100,
                },
                x_lims=(0,400),
                y_lims=(0,100))

hwy1_power = power_consumer(s=1, task="hwy", consumption=consumption_calc(0, "hwy", [0.30, 0.32], 0, 20))
print(f"Contract hwy1_power:\n\n{hwy1_power}")

graph7 = plot_guarantees_with_bounds_hover(contract=hwy1_power,
                x_var=Var("distance_hwy1"),
                y_var=Var("soc1_final"),
                var_values={
                  Var("soc1_initial"):100,
                },
                x_lims=(0,400),
                y_lims=(0,100))

plt.show()

# cty2_power = power_consumer(s=3, task="cty2", consumption=consumption_calc("500", "cty"))
# print(f"Contract cty2_power:\n\n{cty2_power}")

# graph2 = plot_guarantees_with_bounds_hover(contract=cty2_power,
#                 x_var=Var("distance_cty2"),
#                 y_var=Var("soc2_final"),
#                 var_values={
#                   Var("soc2_initial"):100,
#                 },
#                 x_lims=(0,0.172),
#                 y_lims=(0,100))

# plt.show()

# hwy1_power = power_consumer(s=2, task="hwy", consumption=consumption_calc("0", "hwy"))
# print(f"Contract hwy1_power:\n\n{hwy1_power}")

# graph2 = plot_guarantees_with_bounds_hover(contract=hwy1_power,
#                 x_var=Var("distance_hwy1"),
#                 y_var=Var("soc1_final"),
#                 var_values={
#                   Var("soc1_initial"):80,
#                 },
#                 x_lims=(0,400),
#                 y_lims=(0,80))

# plt.show()

# cty1_power = power_consumer(s=3, task="cty", consumption=consumption_calc("0", "cty"))
# print(f"Contract cty1_power:\n\n{cty1_power}")

# graph3 = plot_guarantees_with_bounds_hover(contract=cty1_power,
#                 x_var=Var("distance_cty3"),
#                 y_var=Var("soc3_final"),
#                 var_values={
#                   Var("soc3_initial"):100,
#                 },
#                 x_lims=(0,500),
#                 y_lims=(0,100))

# plt.show()

# steps12=scenario_sequence(c1=hwy1_power, c2=charging1_power, variables=["soc"], c1index=1)
# print(f"---- L2R Steps 1,2\n{steps12}")
# print('\n'.join(bounds(steps12)))

# steps23=scenario_sequence(c1=charging1_power, c2=cty1_power, variables=["soc"], c1index=2)
# print(f"---- L2R Steps 2,3\n{steps23}")
# print('\n'.join(bounds(steps23)))

# steps1_23=scenario_sequence(c1=hwy1_power, c2=steps23, variables=["soc"], c1index=1)
# print(f"---- L2R Steps 1 and 2,3\n{steps1_23}")
# print('\n'.join(bounds(steps1_23)))

# steps123=scenario_sequence(c1=steps12, c2=cty1_power, variables=["soc"], c1index=2)
# print(f"---- L2R Steps 1,2,3\n{steps123}")
# print('\n'.join(bounds(steps123)))

# steps1234=scenario_sequence(c1=steps123, c2=hwy2_power, variables=["soc"], c1index=3)
# print(f"---- L2R Steps 1,2,3,4\n{steps1234}")
# print('\n'.join(bounds(steps1234)))

