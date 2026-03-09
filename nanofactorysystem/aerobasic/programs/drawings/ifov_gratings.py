from idlelib.colorizer import matched_named_groups
from typing import Iterator

import numpy as np

from nanofactorysystem.aerobasic.programs.drawings import DrawableObject, DrawableAeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.base import IFOV_AeroBasicProgram
from nanofactorysystem.aerobasic.programs.drawings.lines import HatchingDirection, XLines, Rectangle3D, IFOV_Lines
from nanofactorysystem.devices.coordinate_system import Point3D, Point2D, CoordinateSystem


class HeightFunctionStructure(DrawableObject):
    """
    Base class for height-function-based structures.

    Subclasses must implement:
    - _create_height_function() -> Callable
    - _get_z_range() -> Tuple[float, float]
    """

    def __init__(
            self,
            center: Union[Point2D, Point3D],
            width: float,
            length: float,
            *,
            hatch_size: float,
            slice_size: float,
            velocity: float,
            acceleration: float,
            aperture: Optional[Callable] = None,
            hatch_angle_deg: float = 0.0,
            alternating_hatch: bool = True,
            hatch_angle_increment: float = 90.0,
            fov_size: Tuple[float, float] = (150.0, 150.0),
            usable_fov_fraction: float = 0.85,
            grid_resolution: int = 500
    ):
        super().__init__()

        self.center = center
        self.width = width
        self.length = length
        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration
        self.aperture = aperture
        self.hatch_angle_deg = hatch_angle_deg
        self.alternating_hatch = alternating_hatch
        self.hatch_angle_increment = hatch_angle_increment
        self.fov_size = fov_size
        self.usable_fov_fraction = usable_fov_fraction
        self.grid_resolution = grid_resolution

        if grid_resolution > 2000:
            warnings.warn(
                f"grid_resolution={grid_resolution} is very high. Consider 500-1000.",
                UserWarning
            )

        self._tile_manager: Optional[TileManager] = None
        self._slice_cache: Optional[List[TileSliceResult]] = None
        self._layer_to_tile_mapping: Optional[Dict[int, Dict]] = None

    @property
    def center_point(self) -> Point2D:
        if isinstance(self.center, Point3D):
            return Point2D(self.center.X, self.center.Y)
        return self.center

    @property
    def base_z(self) -> float:
        if isinstance(self.center, Point3D):
            return self.center.Z
        return 0.0

    @property
    def tile_manager(self) -> TileManager:
        if self._tile_manager is not None:
            return self._tile_manager

        self._tile_manager = TileManager(
            structure_size=(self.width, self.length),
            fov=self.fov_size,
            usable_fraction=self.usable_fov_fraction,
            center=self.center_point
        )
        self._tile_manager.calc_parameters()
        self._tile_manager.generate_tiles()

        return self._tile_manager

    @property
    def needs_stitching(self) -> bool:
        return self.tile_manager.needs_stitching()

    @property
    def n_tiles(self) -> int:
        return self.tile_manager.get_n_tiles_total()

    @abstractmethod
    def _create_height_function(self) -> Callable:
        pass

    @abstractmethod
    def _get_z_range(self) -> Tuple[float, float]:
        pass

    def _create_slicer_config(self) -> SlicerConfig:
        return SlicerConfig(
            slice_size=self.slice_size,
            hatch_size=self.hatch_size,
            hatch_angle_deg=self.hatch_angle_deg,
            alternating_hatch=self.alternating_hatch,
            hatch_angle_increment=self.hatch_angle_increment,
            velocity=self.velocity,
            acceleration=self.acceleration,
            grid_resolution=self.grid_resolution
        )

    def _slice_structure(self) -> List[TileSliceResult]:
        if self._slice_cache is not None:
            return self._slice_cache

        slicer = TileAwareSlicer(self._create_slicer_config())
        z_min, z_max = self._get_z_range()

        results = []
        for tile_info in self.tile_manager.get_tile_dict():
            tile_center = tuple(tile_info['center_tile'])

            # Create tile-specific functions
            base_func = self._create_height_function()
            structure_cx, structure_cy = self.center.X, self.center.Y
            offset_x = tile_center[0] - structure_cx
            offset_y = tile_center[1] - structure_cy

            def height_func(X, Y, ox=offset_x, oy=offset_y, bf=base_func):
                return bf(X + ox, Y + oy)

            if self.aperture is not None:
                def aperture_func(X, Y, ox=offset_x, oy=offset_y, ap=self.aperture):
                    return ap(X + ox, Y + oy)
            else:
                aperture_func = None

            result = slicer.slice_tile(
                tile_info=tile_info,
                height_func=height_func,
                z_min=z_min,
                z_max=z_max,
                base_z=self.base_z,
                aperture=aperture_func
            )
            results.append(result)

        self._slice_cache = results
        return results

    def create_move_tile_program(self, x, y, F=None):
        """
        x and y are in mm and velocity F is in mm/s
        """
        pgm = AeroBasicProgram()
        pgm.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
        pgm.MOVEINC(axis=SingleAxis.X, distance=x / 1000, speed=F if F is not None else 10)
        pgm.MOVEINC(axis=SingleAxis.Y, distance=y / 1000, speed=F if F is not None else 10)
        pgm.WAIT(WaitMode.MOVE_DONE)
        pgm.ABSOLUTE()

        return pgm

    def iterate_layers(
            self,
            coordinate_system: CoordinateSystem,
            strategy: str = "TILE_FIRST"
    ) -> Iterator[DrawableAeroBasicProgram]:
        """
        Generate programs for all layers.

        Args:
            coordinate_system: Coordinate system for transformations
            strategy: "TILE_FIRST" or "LAYER_FIRST"
        """
        investigation = True
        if investigation: start1 = datetime.datetime.now()
        tile_results = self._slice_structure()
        if investigation:
            end1 = datetime.datetime.now()
            print(f"TIME for calculating slice of structure:\t{(end1 - start1).seconds}")

        if not tile_results:
            return

        if investigation: start2 = datetime.datetime.now()
        laser_config = LaserSegmentsConfig(
            velocity=self.velocity,
            acceleration=self.acceleration,
            sorting_strategy=SortingStrategy.SERPENTINE,
            use_acceleration_distance=True
        )
        if investigation:
            end2 = datetime.datetime.now()
            print(f"TIME for calculating laser segment config:\t{(end2 - start2).seconds}")

        if strategy == "TILE_FIRST":
            iteration_order = self._generate_tile_first_order(tile_results)
        else:
            iteration_order = self._generate_layer_first_order(tile_results)
        # Initialising Mapping
        self._layer_to_tile_mapping = {}
        layer_counter = 0
        prev_tile_index = None

        if investigation: start3 = datetime.datetime.now()
        for tile_result, slice_result, layer_idx in iteration_order:
            if slice_result.is_empty:
                continue

            tile_x, tile_y = tile_result.tile_center
            self._layer_to_tile_mapping[layer_counter] = {
                'tile_index': tile_result.tile_index,
                'tile_center': (tile_x, tile_y),
                'layer_idx_in_tile': layer_idx
            }
            layer_program = DrawableAeroBasicProgram(coordinate_system)
            tile_x, tile_y = tile_result.tile_center

            layer_program.comment(
                f"\n; Tile {tile_result.tile_index}, Layer {layer_idx}, "
                f"Z={slice_result.z_absolute:.3f}, {strategy}, "
                f"X offset {tile_x}, y offset {tile_y}, "
            )

            # is_new_tile = (tile_result.tile_index != prev_tile_index)
            #
            # if is_new_tile:
            #     # create In-Between-Tile Movement
            #     tile_movement_program = self.create_move_tile_program(tile_x, tile_y, F=self.velocity)
            #     layer_program.add_programm(tile_movement_program)
            #     prev_tile_index = tile_result.tile_index
            #     # todo include programm task number to know when new tiles are being printed

            layer_program.LINEAR(Z=slice_result.z_absolute)

            laser_segments = LaserSegments(
                segments=slice_result.segments,
                config=laser_config
            )

            for segment_program in laser_segments.iterate_layers(coordinate_system):
                layer_program.add_programm(segment_program)

            layer_program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)

            yield layer_program
            layer_counter += 1

        if investigation:
            end3 = datetime.datetime.now()
            print(f"TIME for iteration over all layers (writing programs):\t{(end3 - start3).seconds}")

    def _generate_tile_first_order(self, tile_results):
        for tile_result in tile_results:
            for layer_idx, slice_result in enumerate(tile_result.slices):
                yield (tile_result, slice_result, layer_idx)

    def _generate_layer_first_order(self, tile_results):
        if not tile_results:
            return
        max_layers = max(len(tr.slices) for tr in tile_results)
        for layer_idx in range(max_layers):
            for tile_result in tile_results:
                if layer_idx < len(tile_result.slices):
                    yield (tile_result, tile_result.slices[layer_idx], layer_idx)

    def get_tile_center_for_layer(self, layer_id: int) -> Tuple[float, float]:
        """Gibt tile_center für gegebene layer_id zurück."""
        if self._layer_to_tile_mapping is None:
            raise RuntimeError("iterate_layers() muss erst aufgerufen werden")

        if layer_id not in self._layer_to_tile_mapping:
            raise ValueError(f"Layer {layer_id} existiert nicht")

        return self._layer_to_tile_mapping[layer_id]['tile_center']

    def get_tile_info_for_layer(self, layer_id: int) -> Dict:
        """Gibt vollständige Tile-Info für layer_id zurück."""
        if self._layer_to_tile_mapping is None:
            raise RuntimeError("iterate_layers() muss erst aufgerufen werden")

        return self._layer_to_tile_mapping.get(layer_id)

    def to_json(self) -> Dict[str, Any]:
        return {
            "__class__": self.__class__.__name__,
            "center_point": self.center_point.as_tuple(),
            "__init__": self._init_args(),
            "number tiles": self.n_tiles,
            "tiles": self.tile_manager.to_json()
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self.width}×{self.length}, tiles={self.n_tiles})"


class BinaryGrating(HeightFunctionStructure):
    """Binary (step) grating structure."""

    def __init__(self, center, width, length, period, height,
                 duty_cycle=0.5, grating_angle_deg=0.0, phase_deg=0.0,
                 base_height=0.0, **kwargs):
        super().__init__(center, width, length, **kwargs)
        self.period = period
        self.height = height
        self.duty_cycle = duty_cycle / period if duty_cycle > 1.0 else duty_cycle
        self._duty_cycle_input = duty_cycle
        self.grating_angle_deg = grating_angle_deg
        self.phase_deg = phase_deg
        self.base_height = base_height

    def _create_height_function(self):
        return HeightFunctions.binary_grating(
            period=self.period, height=self.height,
            duty_cycle=self.duty_cycle, angle_deg=self.grating_angle_deg,
            z0=self.base_height, phase_deg=self.phase_deg
        )

    def _get_z_range(self):
        return (self.base_height, self.base_height + self.height)


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
                 acceleration: float,
                 # aperture: Optional[Callable] = None,
                 alternating_hatch: bool = True
                 ):
        super().__init__()
        self.center = center
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.period = period
        self.height = height
        self.duty_cycle = duty_cycle / period if duty_cycle > 1.0 else duty_cycle
        self._duty_cycle_input = duty_cycle
        self.grating_angle_deg = grating_angle_deg
        self.phase_deg = phase_deg
        self.base_height = base_height

        self.hatch_size = hatch_size
        self.slice_size = slice_size
        self.velocity = velocity
        self.acceleration = acceleration

    @property
    def structure_length(self) -> float:
        return self.y_dim

    @property
    def structure_width(self) -> float:
        return self.x_dim

    @property
    def structure_height(self) -> np.array:
        return self.base_height + self.height

    @property
    def center_point(self) -> Point2D:
        return self.center

    @property
    def centers_of_duty_cycles(self):
        # todo : hier soll die berechnung stattfinden in der ich alle center punkte für die binären strukturen (Hochpunkte) berechne
        #   diese werden dann genutzt um in jeder ebene dahin zu fahren
        # POINT3D MUSS
        return[]

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[DrawableAeroBasicProgram]:
        program = DrawableAeroBasicProgram(coordinate_system)
        if self.base_height > 0:
            socket = Rectangle3D_IFOV(
                center=self.center,
                x_length=self.x_dim,
                y_length=self.y_dim,
                height=self.base_height,
                hatch_size=self.hatch_size,
                slice_size=self.slice_size,
                velocity=self.velocity,
                power=self.power,
                angle=self.angle,
                alternate_hatching=self.alternate_hatching,
                hatching_direction=self.start_hatching_direction
            )
            yield from socket.iterate_layers(coordinate_system)

        slice_size_opt =0 # todo

        if self.base_height==0.0:  # accounts for a not defined base_height
            start_z = self.center.Z
        else:
            start_z = self.base_height

        for z_height in np.arange(start_z+slice_size_opt,self.height+slice_size_opt, slice_size_opt):  # +slize weil arange sonst die letzte zahl verschluckt und die base_height wahrscheinlich doppelt gedruckt wird?
            # todo untersuchen ob ich bei dem Ende noch (z_ende +slice) machen muss, oder ob das ohne dessen besser funktioiert in bezug darauf die bessere/ genauere höhe zu bekommen
            # todo überprüfen ob die base_height layer doppelt gedruckt werden würde

            # maybe include z-coordinate in rect2d - then no extra point has to be done here
            for center_point_duty_cycle in self.centers_of_duty_cycles:
                # wenn z-coord in rect2d verfahren wird:
                # center_pointBLA.Z = z_height

                # dann einfach nur rect2d machen und programm adden
                pass

        # todo wo genau speichert das programm die layer ab? ich muss ja gucken, dass es später integrierbar bleibt mit dhm
        #   wird das mit yield dann bestimmt? weil dann muss ich hier zum beispiel zwischendurch draw on machen und sonst yield
        #   ich glaub das ist es
        # Add steps
        z_step_offset = self.base_height

        for step_x in range(self.x_steps):
            for step_y in range(self.y_steps):
                x_offset = -self.x_steps / 2 * self.feature_width + step_x * self.feature_width + self.feature_width / 2
                y_offset = -self.y_steps / 2 * self.feature_length + step_y * self.feature_length + self.feature_length / 2
                slice_size_opt = self.height_profile[step_y][step_x] / round(
                    self.height_profile[step_y][step_x] / self.slice_size)

                step_rectangle = Rectangle3D(
                    center=self.center + Point3D(x_offset, y_offset, z_step_offset),
                    width=self.feature_width,
                    length=self.feature_length,
                    height=self.height_profile[step_y][step_x],
                    hatch_size=self.hatch_size,
                    slice_size=slice_size_opt,
                    velocity=self.velocity,
                    acceleration=self.acceleration
                )

                yield from step_rectangle.iterate_layers(coordinate_system)

        return program


class Rectangle2D_IFOV(DrawableObject):

    def __init__(
            self,
            center: Point2D | Point3D, # todo check if it is better to have a 3D point and to always go to z coordinate as well
            x_length: float,
            y_length: float,
            *,
            hatch_size: float,
            velocity: float,
            power:float = None,
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
        self.power =power
        self.hatching_direction = hatching_direction

    @property
    def center_point(self) -> Point2D:
        return self.center

    def iterate_layers(self, coordinate_system: CoordinateSystem) -> Iterator[IFOV_AeroBasicProgram]:
        #todo
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

        yield from ifov_lines.iterate_layers(coordinate_system)


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
            angle:float = 0.0,
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
        # todo: i dont know exactly why i added Z==0 here. maybe rethink in future - 02.12 HOTFIX
        # if self.height == 0 and self.center.Z==0:
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
            program = DrawableAeroBasicProgram(coordinate_system)
            program.RAPID(Z=z_offset + self.center.Z)  # todo (HR) check if it has an influence if LINEAR is used - out of the scope of IFOV should be working
            program.add_programm(rectangle.draw_on(coordinate_system))
            yield program
            if self.alternate_hatching:
                self.hatching_direction.flip()  # todo - is it really flipping the x|y axes?
