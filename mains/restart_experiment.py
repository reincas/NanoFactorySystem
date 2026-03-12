import numpy as np
from pathlib import Path
from nanofactorysystem import getLogger
from nanofactorysystem.devices.coordinate_system import DropDirection, Point2D, Point3D
from nanofactorysystem.experiment import Experiment, StructureType

def load_experiment_parameter(path):
    # dummy funktion akutell
    user = "Hannes"
    sys_args = {
            "attenuator": {
                "fitKind": "quadratic",
            },
            "sample": {
                "name": "#1",
                "orientation": "top",
                "substrate": "boro-silicate glass",
                "substrateThickness": 700.0,
                "material": "SZ2080",
                "materialThickness": 75.0,
            },
            "focus": {
                "OffsetFocusDetection": [130, -15],
                # "OffsetFocusDetection": [120, -80],
                "minCircularity": 0.8,
                "exposureValue": 120,
                "minDiffMax": 10.0  # Wert für 20x - ToDO für 63x genauso?
            },
            "layer": {
                # "beta": 0.7,
                "dzFineDefault": 25.0,
                "laserPower": 0.7,
            },
            "plane": {},
        }

    zmax = 25350.0
    sys_args.update({"controller": {
        "zMax": zmax, }
    })
    if "dhm" in sys_args.keys():
        sys_args["dhm"].update({"usage": False})
    else:
        sys_args.update({"dhm": {"usage": False}})

    resin_dimension = [
        [200, 19200],  # right edge
        [300, 25800],  # left edge
        [-3600, 22800],  # near edge
        [3300, 22400]  # far edge
    ]
    center = Point2D(X=0,  #
                     Y=22000)  #

    edges = np.asarray(resin_dimension)
    resin_corner_tr = Point2D(*np.max(edges, axis=0))
    resin_corner_bl = Point2D(*np.min(edges, axis=0))
    absolute_grid_center = center

    grid_size = (2, 1)
    structure_size=300
    drop_direction = DropDirection.UP
    fov = 500
    zmax = 25350.0
    # Corner settings
    c_width = 50
    c_length = 300
    c_height = 7
    c_hatch = 0.5
    c_slice = 0.75
    # printing area settings
    margin = 200
    padding = 100
    # printing settings
    movement_axis = ["ABZ", "XYZ"]
    parameterset = {
        "hatch size": 0.25,  # hatch size
        "slice size": 0.3,  # slice size/ layer height
        "power": 0.7,
        "velocity": 5_000
    }
    exp_dict = {"path": Path(path),
        "user": user,
        "objective": "Zeiss 20x",
        "logger": getLogger(logfile=f"{path}/console.log"),
        "sys_args": sys_args,
        "default_power": 0.7,
        "low_speed_um": 2_000,
        "high_speed_um": 10_000,
        "resin_corner_tr": resin_corner_tr,
        "resin_corner_bl": resin_corner_bl,
        "structure_size": structure_size,
        "margin": margin,
        "padding": padding,
        "absolute_grid_center": absolute_grid_center,
        "grid_size": grid_size,
        "n_mid_points": 0,
        "drop_direction": drop_direction,
        "corner_z": -2,
        "corner_width":c_width,
        "corner_length":c_length,
        "corner_height":c_height,
        "corner_hatch":c_hatch,
        "corner_slice":c_slice,
        "fov_dim":(fov, fov),
        "skip_corner": False,
        "plane_fit_mode": 1,
        "setup": "IFOV_off"
    }
    return exp_dict



# todo
#       create dictionary for restarting experiment  - alles was am anfang dem Experiment übergeben wird
#       übergabe von restart sollte eigentlich nur die ordner struktur sein
#       zusätzlich muss außerdem noch die substrat informationen im hauptordner gegeben werden
#       !!! Experiment bekommt immer eine neue UUID - das sollte nicht sein!

main_path =r""  # aktuell nicht gebraucht , da egal
exp_path = r"C:\Users\Nanofactory\Desktop\Hannes\Experiment data\test2_program\TEST_aerotech_1"

exp_paras = load_experiment_parameter(exp_path)

with Experiment(
            path=exp_paras["path"],
            user=exp_paras["user"],
            objective=exp_paras["objective"],
            logger=exp_paras["logger"],
            sys_args=exp_paras["sys_args"],
            default_power=exp_paras["default_power"],
            low_speed_um=exp_paras["low_speed_um"],
            high_speed_um=exp_paras["high_speed_um"],
            resin_corner_tr=exp_paras["resin_corner_tr"],
            resin_corner_bl=exp_paras["resin_corner_bl"],
            structure_size=exp_paras["structure_size"],
            margin=exp_paras["margin"],
            padding=exp_paras["padding"],
            absolute_grid_center=exp_paras["absolute_grid_center"],
            grid=exp_paras["grid_size"],
            n_mid_points=exp_paras["n_mid_points"],
            drop_direction=exp_paras["drop_direction"],
            corner_z=exp_paras["corner_z"],
            corner_width=exp_paras["corner_width"],
            corner_length=exp_paras["corner_length"],
            corner_height=exp_paras["corner_height"],
            corner_hatch=exp_paras["corner_hatch"],
            corner_slice=exp_paras["corner_slice"],
            fov_dim=exp_paras["fov_dim"],
            plane_fit_mode=exp_paras["plane_fit_mode"],
            skip_corner=exp_paras["skip_corner"],) as experiment:
    experiment.restart_experiment()

    # todo nochmal kontrollieren, wenn er bereits eine oder zwis schichten gedruckt hat - sieht so aus, dass es nicht an der richtigen stelle wieder startet!
    # wahrscheinlich liegt es daran, wenn das abbricht nachdem man bereits einmal wieder aufgestartete hat, dann wird die anzahl der layer geändert

