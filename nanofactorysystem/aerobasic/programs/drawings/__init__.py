import abc
from typing import Optional, Any

from nanofactorysystem.aerobasic import SingleAxis, BezierMode, Axis, GalvoLaserOverrideMode
from nanofactorysystem.aerobasic.programs import AeroBasicProgram
from nanofactorysystem.devices.coordinate_system import CoordinateSystem, Point2D, Point3D


class DrawableAeroBasicProgram(AeroBasicProgram):
    def __init__(self, coordinate_system: CoordinateSystem):
        super().__init__()
        self.coordinate_system = coordinate_system

    def LINEAR(
            self,
            X: Optional[float] = None,
            Y: Optional[float] = None,
            Z: Optional[float] = None,
            A: Optional[float] = None,
            B: Optional[float] = None,
            F: Optional[float] = None,
            E: Optional[float] = None
    ):
        coordinate = {
            "X": X,
            "Y": Y,
            "Z": Z,
            "A": A,
            "B": B,
        }
        coordinate = {k: v for k, v in coordinate.items() if v is not None}
        converted_coordinate = self.coordinate_system.convert(coordinate)

        if F is not None:
            F *= self.coordinate_system.unit.value
        if E is not None:
            E *= self.coordinate_system.unit.value
        return super().LINEAR(**converted_coordinate, F=F, E=E)

    def CW(
            self,
            axis1: SingleAxis,
            axis1_endpoint: float,
            axis2: SingleAxis,
            axis2_endpoint: float,
            radius: Optional[float] = None,
            axis1_center: Optional[float] = None,
            axis2_center: Optional[float] = None,
            velocity: float = None
    ):
        return super().CW(
            **self._convert_CW_CCW_args(
                axis1=axis1,
                axis1_endpoint=axis1_endpoint,
                axis2=axis2,
                axis2_endpoint=axis2_endpoint,
                radius=radius,
                axis1_center=axis1_center,
                axis2_center=axis2_center,
                velocity=velocity
            )
        )

    def CCW(
            self,
            axis1: SingleAxis,
            axis1_endpoint: float,
            axis2: SingleAxis,
            axis2_endpoint: float,
            radius: Optional[float] = None,
            axis1_center: Optional[float] = None,
            axis2_center: Optional[float] = None,
            velocity: float = None
    ):
        return super().CCW(
            **self._convert_CW_CCW_args(
                axis1=axis1,
                axis1_endpoint=axis1_endpoint,
                axis2=axis2,
                axis2_endpoint=axis2_endpoint,
                radius=radius,
                axis1_center=axis1_center,
                axis2_center=axis2_center,
                velocity=velocity
            )
        )

    def _convert_CW_CCW_args(
            self,
            axis1: SingleAxis,
            axis1_endpoint: float,
            axis2: SingleAxis,
            axis2_endpoint: float,
            radius: Optional[float] = None,
            axis1_center: Optional[float] = None,
            axis2_center: Optional[float] = None,
            velocity: float = None
    ):
        # Map axes
        axis1_mapped = self.coordinate_system.axis_mapping.get(axis1.parameter_name, axis1.parameter_name)
        axis2_mapped = self.coordinate_system.axis_mapping.get(axis2.parameter_name, axis2.parameter_name)

        # Convert endpoints
        axis1_endpoint = self.coordinate_system.convert({axis1.parameter_name: axis1_endpoint})[axis1_mapped]
        axis2_endpoint = self.coordinate_system.convert({axis2.parameter_name: axis2_endpoint})[axis2_mapped]

        # Convert radius
        if radius is not None:
            radius *= self.coordinate_system.unit.value

        # Convert axis center
        if axis1_center is not None:
            # axis1_center = self.coordinate_system.convert({axis1.parameter_name: axis1_center})[axis1_mapped]
            axis1_center = axis1_center * self.coordinate_system.unit.value
        if axis2_center is not None:
            # axis2_center = self.coordinate_system.convert({axis2.parameter_name: axis2_center})[axis2_mapped]
            axis2_center = axis2_center * self.coordinate_system.unit.value

        # Convert velocity
        if velocity is not None:
            velocity *= self.coordinate_system.unit.value

        return {
            'axis1': Axis(axis1_mapped),
            'axis1_endpoint': axis1_endpoint,
            'axis2': Axis(axis2_mapped),
            'axis2_endpoint': axis2_endpoint,
            'radius': radius,
            'axis1_center': axis1_center,
            'axis2_center': axis2_center,
            'velocity': velocity
        }

    def BEZIER(
            self,
            mode: BezierMode,
            ax_h: SingleAxis,
            ax_v: SingleAxis,
            p0_h: float,
            p1_h: float,
            p2_h: float,
            p3_h: Optional[float],
            p0_v: float,
            p1_v: float,
            p2_v: float,
            p3_v: Optional[float],
            tolerance: Optional[float]
    ):
        raise NotImplemented("To be done")


class DrawableObject(abc.ABC):
    def __init__(self):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__} at {self.center_point}"

    @property
    @abc.abstractmethod
    def center_point(self) -> Point2D:
        pass

    @abc.abstractmethod
    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        pass

    def _init_args(self) -> dict[str, Any]:
        code = self.__init__.__code__
        if "__init__" not in code.co_names:
            return {}

        start_idx = code.co_names.index("__init__") + 1
        kwargs = {}
        for name in code.co_names[start_idx:start_idx + code.co_argcount]:
            attr = getattr(self, name, "[NOT FOUND]")
            if attr == "[NOT FOUND]":
                continue
            if hasattr(attr, "to_json"):
                attr = attr.to_json()
            elif not isinstance(attr, (str, int, float, dict, list)) or attr is not None:
                attr = str(attr)

            kwargs[name] = attr
        return kwargs

    def to_json(self):
        return {
            "__class__": self.__class__.__name__,
            "center_point": self.center_point.as_tuple(),
            "__init__": self._init_args()
        }


class VoidStructure(DrawableObject):
    """ Structure that does nothing """

    @property
    def center_point(self) -> Point2D:
        return Point2D(0, 0)

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        return DrawableAeroBasicProgram(coordinate_system)


class DrawablePoint(DrawableObject):
    def __init__(
            self,
            center: Point2D | Point3D,
            duration: float = 0.1
    ):
        """
        duration in seconds
        """
        super().__init__()
        self.center = center
        self.duration = duration

    @property
    def center_point(self) -> Point2D:
        return self.center

    def draw_on(self, coordinate_system: CoordinateSystem) -> DrawableAeroBasicProgram:
        program = DrawableAeroBasicProgram(coordinate_system)
        program.LINEAR(**self.center.as_dict())
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.ON)
        program.DWELL(self.duration)
        program.GALVO_LASER_OVERRIDE(GalvoLaserOverrideMode.OFF)
        return program
