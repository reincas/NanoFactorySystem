from idlelib.colorizer import matched_named_groups
from typing import Iterator

import numpy as np

from nanofactorysystem.aerobasic import SingleAxis
from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.base import IFOV_AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import HatchingDirection, IFOV_Lines
from nanofactorysystem.devices.coordinate_system import Point3D, Point2D, CoordinateSystem


class BinaryGrating_IFOV(DrawableObject):
    def __init__(self,
                 center: Point3D,
                 x_dim: float,
                 y_dim: float,
                 period: float,
                 height: float,
                 duty_cycle=0.5,
                 grating_angle_deg=0.0,
                 phase_deg=0.0,  # starting point for phase
                 base_height=0.0,
                 *,
                 hatch_size: float,
                 slice_size: float,
                 velocity: float,
                 power: float,
                 start_hatching_direction: HatchingDirection = HatchingDirection.X,
                 # aperture: Optional[Callable] = None,
                 alternating_hatch: bool = True
                 ):
        """
        -------------------------------------       -               -           │
        │                x                  │ periode length    duty_cycle (%)  │
        -------------------------------------       │               -           v
        -->            x_dim              <--       │                         y_dim
        -------------------------------------      ---                          ^
        │                x                  │                                   │
        -------------------------------------                                   │
                                                                                │
        ...                                                                    ...

        y_dim ...       defines the amount of periods of the structure. e.g.: 500µm x_dim with 20µm period -> 25 times
                        one full cycle.
        x-dim ...       defines the width of the grating
        height ...      is the height of the grating (duty cycle)
        duty_cycle ...  is the duty cycle in percent of one period. e.g.: 0.75 duty_cycle with 20µm period means 5µm of
                        low cycle and 15µm of high cycle (0.75*20)
        base_height ... is the base height of the grating = height of low cycle of the grating
        phase_deg ...   is the starting phase of the grating -> phase degree=90 means that we start at 1/4 of the period
                        cycle. if the duty cycle is e.g. also 1/4 then it means that we start with a low cycle.
        grating_angle_deg ...  is the grating angle in degrees
        alternate_hatching ... bool if hatching should be switching from layer to layer.

        printing parameters:
            - hatch_size: Hatch size of the grating - distance between lines
            - slice_size: size of layer height
            - velocity: velocity of printing of the connected axes
            - power: power to be set - has to be a float and be between 0 and 10 depending on the calibration of the
                    system
            - start_hatching_direction: direction of the hatching in the first layer.

        """
        super().__init__()
        self.center = center
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.period = period
        self.height = height
        self.duty_cycle = duty_cycle / period if duty_cycle > 1.0 else duty_cycle
        self.duty_width = self.duty_cycle * self.period
        self._duty_cycle_input = duty_cycle
        self.grating_angle_deg = grating_angle_deg
        self.phase_deg = phase_deg
        self.base_height = base_height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.power = power
        self.start_hatching_direction = start_hatching_direction
        self.alternating_hatch = alternating_hatch

        self._center_points_duty_cycle = None

    @property
    def structure_length(self) -> float:
        return self.y_dim

    @property
    def structure_width(self) -> float:
        return self.x_dim

    @property
    def structure_height(self) -> float:
        return self.base_height + self.height + self.center.Z

    @property
    def center_point(self) -> Point2D:
        return self.center

    @property
    def n_periods(self) -> float:
        return self.y_dim / self.period

    @property
    def centers_of_duty_cycles(self, force=False):
        if self._center_points_duty_cycle is None or force:
            center_points = []
            whole_period_end = self.n_periods == int(self.n_periods)

            for i in range(int(self.n_periods)):
                k = self.y_dim / 2 - self.duty_width / 2 - i * self.period
                if i == int(self.n_periods - 1):
                    if not whole_period_end:
                        # last period and is not an entire period, so k has to be re-calculated
                        k = -self.y_dim / 2 + round(self.n_periods % 1, 5) / 2 * self.period
                x_coord = self.center.X - k * np.sin(self.grating_angle_deg)
                y_coord = self.center.Y - k * np.cos(self.grating_angle_deg)
                center = Point3D(X=x_coord, Y=y_coord, Z=0)
                center_points.append(center)
            self._center_points_duty_cycle = center_points

        return self._center_points_duty_cycle

    def iterate_layers(self, coordinate_system: CoordinateSystem,
                       full_layer_yield=False
                       ) -> Iterator[IFOV_AeroBasicProgram|DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.base_height > 0:
            base = Rectangle3D_IFOV(
                center=self.center,
                x_length=self.x_dim,
                y_length=self.y_dim,
                height=self.base_height,
                hatch_size=self.hatch_size,
                slice_size=self.slice_size,
                velocity=self.velocity,
                power=self.power,
                angle=self.grating_angle_deg,
                alternate_hatching=self.alternating_hatch,
                hatching_direction=self.start_hatching_direction
            )
            yield from base.iterate_layers(coordinate_system)

        n_layer = abs(round(self.height / self.slice_size)) + 1
        slice_size_opt = self.height / (n_layer - 1)

        if self.base_height == 0.0:  # accounts for a not defined base_height
            start_z = self.center.Z
        else:
            start_z = self.base_height + self.center.Z

        for z_height in np.arange(start_z + slice_size_opt, self.structure_height + slice_size_opt,
                                  slice_size_opt):
            # +slize weil arange sonst die letzte zahl verschluckt und die base_height wahrscheinlich doppelt gedruckt wird?
            # todo untersuchen ob ich bei dem Ende noch (z_ende +slice) machen muss, oder ob das ohne dessen besser funktioiert in bezug darauf die bessere/ genauere höhe zu bekommen
            # todo überprüfen ob die base_height layer doppelt gedruckt werden würde

            layer_program = DrawableAeroBasicProgram(coordinate_system)
            # z-coordinate movement in rect2d
            for center_point_duty_cycle in self.centers_of_duty_cycles:
                center_point = Point3D(X=center_point_duty_cycle.X, Y=center_point_duty_cycle.Y, Z=z_height)
                rectangle = Rectangle2D_IFOV(
                    center=center_point,
                    x_length=self.x_dim,
                    y_length=self.period,
                    hatch_size=self.hatch_size,
                    velocity=self.velocity,
                    power=self.power,
                    hatching_direction=self.start_hatching_direction,
                    angle=self.grating_angle_deg
                )
                if full_layer_yield:
                    layer_program.add_programm(rectangle.draw_on(coordinate_system))
                else:
                    yield from rectangle.iterate_layers(coordinate_system)
                # program.add_programm(rectangle.draw_on(coordinate_system))
                # this will be added to only one file

            if full_layer_yield:
                program.add_programm(layer_program)
                # yielding full layer program with every 2D rectangle
                yield layer_program

        return program


class Rectangle2D_IFOV(DrawableObject):

    def __init__(
            self,
            center: Point2D | Point3D,
            x_length: float,
            y_length: float,
            *,
            hatch_size: float,
            velocity: float,
            power: float = None,
            hatching_direction: HatchingDirection,
            angle: float = 0.0
    ):
        super().__init__()
        self.center = center
        self.x_length = x_length
        self.y_length = y_length
        self.phi = angle

        self.hatch_size = hatch_size
        self.velocity = velocity
        self.power = power
        self.hatching_direction = hatching_direction

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[IFOV_AeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        # top_left = self.center + Point2D(X=-self.x_length/2*np.cos(self.phi), Y=self.y_length/2*np.sin(self.phi))

        if self.hatching_direction == HatchingDirection.X:  # kontinuierliche Linien in y Richtung , hatching entlang der x achse
            hatching_length = self.x_length
            length = self.y_length
            angle = self.phi
        elif self.hatching_direction == HatchingDirection.Y:  # kontinuierliche Linien in x Richtung , hatching entlang der y achse
            hatching_length = self.y_length
            length = self.x_length
            angle = self.phi - 90
        else:
            raise ValueError(f"HatchingDirection not found: {self.hatching_direction}")

        n_hatch = round(hatching_length / self.hatch_size) + 1  # np.ceil()
        hatch_size_opt = hatching_length / (n_hatch - 1)

        order = 1
        lines = []
        # ausrechnen aller Start und Endpunkte des Rechtecks
        for j in range(n_hatch):
            lines.append(
                [
                    Point2D(X=-length / 2 * np.cos(angle) + j * hatch_size_opt * np.sin(angle),
                            Y=-hatching_length / 2 * np.sin(angle) + j * hatch_size_opt * np.cos(angle)),
                    Point2D(X=length / 2 * np.cos(angle) + j * hatch_size_opt * np.sin(angle),
                            Y=-hatching_length / 2 * np.sin(angle) + j * hatch_size_opt * np.cos(angle))
                ][::order]

                # Note i think without center point because of ifov + relative/absolute relationship
                # [self.center+Point2D(X=-length/2 * np.cos(angle) + j * hatch_size_opt *np.sin(angle),
                #                      Y=-hatching_length/2 * np.sin(angle) + j * hatch_size_opt *np.cos(angle)),
                # self.center + Point2D(X=length / 2 * np.cos(angle) + j * hatch_size_opt * np.sin(angle),
                #                Y=-hatching_length / 2 * np.sin(angle) + j * hatch_size_opt * np.cos(angle))
                # ][::order]
            )
            order *= -1

        ifov_lines = IFOV_Lines(
            reference_point=self.center,
            lines=lines,
            velocity=self.velocity,
            power=self.power,
        )
        program.add_programm(ifov_lines.draw_on(coordinate_system))
        yield program


class Rectangle3D_IFOV(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            x_length: float,
            y_length: float,
            height: float,
            *,
            hatch_size: float,
            slice_size: float,
            velocity: float,
            angle: float = 0.0,
            power: float = None,
            alternate_hatching: bool = False,
            hatching_direction: HatchingDirection = HatchingDirection.X
    ):
        super().__init__()
        self.center = center
        self.x_length = x_length
        self.y_length = y_length
        self.height = height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.power = power
        self.alternate_hatching = alternate_hatching
        self.hatching_direction = hatching_direction
        self.angle = angle

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.height == 0:
            yield program

        n_layer = abs(round(self.height / self.slice_size)) + 1
        slice_size_opt = self.height / (n_layer - 1)

        for i in range(n_layer):
            z_offset = i * slice_size_opt
            rectangle = Rectangle2D_IFOV(
                center=self.center + Point3D(0, 0, z_offset),
                x_length=self.x_length,
                y_length=self.y_length,
                hatch_size=self.hatch_size,
                velocity=self.velocity,
                power=self.power,
                hatching_direction=self.hatching_direction,
                angle=self.angle
            )
            program = DrawableAeroBasicProgram(coordinate_system)  # todo ist das notwendig
            
            # FEEEEEHLLLLLEEEERRRR  -- das ist nicht die korrekt z-ccord - sie ist RELATIV und NICHT absolut
            # program.RAPID(Z=z_offset + self.center.Z)
            # todo (HR) check if it has an influence if LINEAR is used - out of the scope of IFOV should be working

            program.add_programm(rectangle.draw_on(coordinate_system))
            yield program
            if self.alternate_hatching:
                self.hatching_direction = self.hatching_direction.flip()
