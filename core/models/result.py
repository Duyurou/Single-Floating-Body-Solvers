"""求解器结果和三维场景的类型合同。

结果模型只保存元数据和有明确类型的数值序列，不负责解析文件，也不负责
渲染场景。这样 parser 可以返回这些对象，而 Service、图表和三维控件不必
依赖某一种具体 OUTPUT 文件格式。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal, Mapping, Sequence, TypeAlias

# 核心合同暂时使用标准库的不可变序列。
# parser 可以在内部使用 NumPy/memmap，跨过合同边界时再转换为这里的值。
# 这样模型包不会强迫每个安装环境都依赖大型数值库。
FloatArray: TypeAlias = tuple[float, ...]
FloatMatrix: TypeAlias = tuple[tuple[float, ...], ...]
AxisKind: TypeAlias = Literal[
    "time",
    "frequency",
    "arc_length",
    "direction",
    "degree_of_freedom",
    "node",
    "custom",
]
CurveDomain: TypeAlias = Literal["time", "frequency", "arc_length"]


def _readonly_array(
    values: Sequence[float],
    *,
    ndim: int | None = None,
) -> FloatArray:
    """把数值向量规范化为不可变、带明确类型的元组。"""

    if ndim not in (None, 1):
        raise ValueError("one-dimensional values are required")
    normalized = tuple(float(value) for value in values)
    if not all(math.isfinite(value) for value in normalized):
        raise ValueError("numeric result arrays must contain finite values")
    return normalized


def _readonly_matrix(values: Sequence[Sequence[float]]) -> FloatMatrix:
    """把数值矩阵规范化为不可变的规则矩阵元组。"""

    matrix = tuple(_readonly_array(row) for row in values)
    width = len(matrix[0]) if matrix else 0
    if any(len(row) != width for row in matrix):
        raise ValueError("matrix rows must have the same length")
    return matrix


def _validate_identifier(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class UnitSpec:
    """单位标签，以及可选的 SI 换算比例。"""

    symbol: str
    quantity: str = ""
    scale_to_si: float = 1.0

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("unit symbol must not be empty")
        if not math.isfinite(self.scale_to_si) or self.scale_to_si <= 0:
            raise ValueError(
                "unit scale_to_si must be a positive finite number",
            )


@dataclass(frozen=True, slots=True)
class CoordinateSystem:
    """结果或场景使用的坐标和角度约定。"""

    name: str = "global"
    length_unit: str = "m"
    angle_unit: str = "deg"
    up_axis: Literal["x", "y", "z"] = "z"

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "coordinate system name")
        _validate_identifier(self.length_unit, "length unit")
        _validate_identifier(self.angle_unit, "angle unit")


@dataclass(frozen=True, slots=True)
class Vector3:
    """带明确类型的三维点或向量。"""

    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        if not all(math.isfinite(value) for value in (self.x, self.y, self.z)):
            raise ValueError("vector coordinates must be finite")

    def as_array(self) -> FloatArray:
        return _readonly_array([self.x, self.y, self.z], ndim=1)


@dataclass(frozen=True, slots=True)
class EulerAngles:
    """按照坐标系角度单位表示的横摇、纵摇和艏摇。"""

    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(value) for value in (self.roll, self.pitch, self.yaw)
        ):
            raise ValueError("rotation angles must be finite")

    def as_array(self) -> FloatArray:
        return _readonly_array([self.roll, self.pitch, self.yaw], ndim=1)


@dataclass(frozen=True, slots=True)
class Pose:
    """物体在指定坐标系中的位置和姿态。"""

    position: Vector3 = field(default_factory=lambda: Vector3(0.0, 0.0, 0.0))
    rotation: EulerAngles = field(default_factory=EulerAngles)
    coordinate_system: CoordinateSystem = field(
        default_factory=CoordinateSystem,
    )


@dataclass(frozen=True, slots=True)
class BodyPose:
    """动态 :class:`SceneFrame` 使用的数值姿态。"""

    position: Sequence[float]
    rotation: Sequence[float]
    position_unit: str = "m"
    rotation_unit: str = "deg"

    def __post_init__(self) -> None:
        position = _readonly_array(self.position, ndim=1)
        rotation = _readonly_array(self.rotation, ndim=1)
        if len(position) != 3:
            raise ValueError("body position must contain exactly three values")
        if len(rotation) != 3:
            raise ValueError("body rotation must contain exactly three values")
        _validate_identifier(self.position_unit, "position unit")
        _validate_identifier(self.rotation_unit, "rotation unit")
        object.__setattr__(self, "position", position)
        object.__setattr__(self, "rotation", rotation)


@dataclass(frozen=True, slots=True)
class LinePoint:
    """系泊线或立管上的一个点，用弧长定位。"""

    arc_length: float
    position: Sequence[float]
    point_id: str = ""

    def __post_init__(self) -> None:
        if not math.isfinite(self.arc_length) or self.arc_length < 0:
            raise ValueError("arc_length must be a finite non-negative value")
        position = _readonly_array(self.position, ndim=1)
        if len(position) != 3:
            raise ValueError(
                "line point position must contain exactly three values",
            )
        object.__setattr__(self, "position", position)


@dataclass(frozen=True, slots=True)
class BodyGeometryRef:
    """浮体几何资源的静态引用。"""

    resource_id: str
    pose: Pose = field(default_factory=Pose)
    vertex_count: int | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.resource_id, "body geometry resource_id")
        if self.vertex_count is not None and self.vertex_count < 0:
            raise ValueError("vertex_count cannot be negative")


@dataclass(frozen=True, slots=True)
class CableTopology:
    """一条系泊线或立管的静态拓扑和可选点列。"""

    cable_id: str
    points: tuple[LinePoint, ...] = ()
    cable_kind: Literal["mooring", "riser", "other"] = "other"

    def __post_init__(self) -> None:
        _validate_identifier(self.cable_id, "cable_id")
        previous = -math.inf
        for point in self.points:
            if point.arc_length < previous:
                raise ValueError("cable points must be ordered by arc_length")
            previous = point.arc_length


@dataclass(frozen=True, slots=True)
class AxisInfo:
    """一个结果维度的元数据和坐标值。"""

    axis_key: str
    values: FloatArray
    label: str = ""
    unit: str | None = None
    kind: AxisKind = "custom"

    def __post_init__(self) -> None:
        _validate_identifier(self.axis_key, "axis_key")
        values = _readonly_array(self.values, ndim=1)
        if len(values) > 1 and any(
            current < previous for previous, current in zip(values, values[1:])
        ):
            raise ValueError(
                "axis values must be monotonically non-decreasing",
            )
        if self.kind == "arc_length" and any(value < 0 for value in values):
            raise ValueError("arc_length axis values must be non-negative")
        object.__setattr__(self, "values", values)

    @property
    def size(self) -> int:
        return len(self.values)


@dataclass(frozen=True, slots=True)
class VariableInfo:
    """结果数据集中一个标量或向量分量的说明。"""

    name: str
    unit: str | None = None
    label: str = ""
    description: str = ""
    coordinate_system: CoordinateSystem | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.name, "variable name")


@dataclass(frozen=True, slots=True)
class AxisSelection:
    """按索引或坐标值选择一个固定的轴位置。"""

    axis_key: str
    index: int | None = None
    value: float | int | str | None = None

    def __post_init__(self) -> None:
        _validate_identifier(self.axis_key, "axis_key")
        if self.index is not None and self.index < 0:
            raise ValueError("axis selection index cannot be negative")
        if self.index is not None and self.value is not None:
            raise ValueError(
                "axis selection must use index or value, not both",
            )
        if self.index is None and self.value is None:
            raise ValueError("axis selection requires index or value")


@dataclass(frozen=True, slots=True)
class SliceSelection:
    """加载结果时哪些轴变化、哪些轴固定。"""

    varying_axes: tuple[str, ...] = ()
    fixed_axes: tuple[AxisSelection, ...] = ()

    def __post_init__(self) -> None:
        varying = tuple(self.varying_axes)
        if len(set(varying)) != len(varying):
            raise ValueError("varying_axes must not contain duplicates")
        fixed_keys = tuple(selection.axis_key for selection in self.fixed_axes)
        if len(set(fixed_keys)) != len(fixed_keys):
            raise ValueError("fixed_axes must not contain duplicates")
        if set(varying).intersection(fixed_keys):
            raise ValueError("an axis cannot be varying and fixed")
        object.__setattr__(self, "varying_axes", varying)
        object.__setattr__(self, "fixed_axes", tuple(self.fixed_axes))


@dataclass(frozen=True, slots=True)
class ResultDataset:
    """带索引的结果资源；数值数据按需加载。"""

    # 一个数据集属于一个工况，通过 ID 和 ComputeCase/OUTPUT 建立联系。
    dataset_id: str
    case_id: str
    source_resource_id: str | None = None

    # 这里只建轴和变量目录；真正数值由 parser 在用户查询时按需读取。
    axes: tuple[AxisInfo, ...] = ()
    variables: tuple[VariableInfo, ...] = ()
    result_kind: str = ""
    source_path: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        _validate_identifier(self.dataset_id, "dataset_id")
        _validate_identifier(self.case_id, "case_id")
        axis_keys = tuple(axis.axis_key for axis in self.axes)
        if len(set(axis_keys)) != len(axis_keys):
            raise ValueError("dataset axes must have unique axis_key values")
        variable_names = tuple(variable.name for variable in self.variables)
        if len(set(variable_names)) != len(variable_names):
            raise ValueError("dataset variables must have unique names")
        object.__setattr__(self, "axes", tuple(self.axes))
        object.__setattr__(self, "variables", tuple(self.variables))

    def axis(self, axis_key: str) -> AxisInfo:
        for axis in self.axes:
            if axis.axis_key == axis_key:
                return axis
        raise KeyError(axis_key)

    def variable(self, name: str) -> VariableInfo:
        for variable in self.variables:
            if variable.name == name:
                return variable
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class CurveSeries:
    """一个变量在时间、频率或弧长轴上的曲线。"""

    x: Sequence[float]
    y: Sequence[float]
    x_label: str
    y_label: str
    x_unit: str | None = None
    y_unit: str | None = None
    label: str = ""
    domain: CurveDomain = "time"
    dataset_id: str | None = None
    variable: VariableInfo | None = None

    def __post_init__(self) -> None:
        x = _readonly_array(self.x, ndim=1)
        y = _readonly_array(self.y, ndim=1)
        if len(x) != len(y):
            raise ValueError("curve x and y arrays must have the same length")
        if self.domain == "arc_length" and any(value < 0 for value in x):
            raise ValueError("arc-length curve x values must be non-negative")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)

    @property
    def point_count(self) -> int:
        return len(self.x)


@dataclass(frozen=True, slots=True)
class MatrixData:
    """带行列标签的二维结果矩阵。"""

    row_labels: tuple[str, ...]
    column_labels: tuple[str, ...]
    values: Sequence[Sequence[float]]
    unit: str | None = None
    label: str = ""
    row_axis: AxisInfo | None = None
    column_axis: AxisInfo | None = None

    def __post_init__(self) -> None:
        values = _readonly_matrix(self.values)
        rows = tuple(self.row_labels)
        columns = tuple(self.column_labels)
        if len(values) != len(rows) or any(
            len(row) != len(columns) for row in values
        ):
            raise ValueError(
                "matrix shape must match row_labels and column_labels lengths",
            )
        if self.row_axis is not None and self.row_axis.size != len(rows):
            raise ValueError("row_axis length must match row_labels")
        if self.column_axis is not None and self.column_axis.size != len(
            columns
        ):
            raise ValueError("column_axis length must match column_labels")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "row_labels", rows)
        object.__setattr__(self, "column_labels", columns)

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.values), len(self.values[0]) if self.values else 0)


@dataclass(frozen=True, slots=True)
class SceneModel:
    """一次结果对应的静态场景拓扑和几何，通常只创建一次。"""

    # 静态几何和拓扑通常只创建一次，播放动画时不重复创建大型对象。
    body_geometries: Mapping[str, BodyGeometryRef] = field(
        default_factory=dict,
    )
    cable_topologies: Mapping[str, CableTopology] = field(default_factory=dict)
    seabed_resource_id: str | None = None
    surface_shape: tuple[int, int] | None = None
    coordinate_system: CoordinateSystem = field(
        default_factory=CoordinateSystem,
    )
    seabed_z: float | None = None
    sea_surface_z: float | None = None

    def __post_init__(self) -> None:
        if self.surface_shape is not None:
            if len(self.surface_shape) != 2 or any(
                size < 1 for size in self.surface_shape
            ):
                raise ValueError(
                    "surface_shape must contain two positive sizes",
                )
        for value, name in (
            (self.seabed_z, "seabed_z"),
            (self.sea_surface_z, "sea_surface_z"),
        ):
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        object.__setattr__(
            self,
            "body_geometries",
            dict(self.body_geometries),
        )
        object.__setattr__(
            self,
            "cable_topologies",
            dict(self.cable_topologies),
        )

    @property
    def body_ids(self) -> tuple[str, ...]:
        return tuple(self.body_geometries)

    @property
    def cable_ids(self) -> tuple[str, ...]:
        return tuple(self.cable_topologies)


@dataclass(frozen=True, slots=True)
class SceneFrame:
    """应用到 :class:`SceneModel` 的一个静态或动态帧。"""

    # 每一帧只保存会变化的数据；静态几何仍然留在 SceneModel 中。
    time: float
    body_poses: Mapping[str, BodyPose] = field(default_factory=dict)
    mooring_points: Mapping[str, Sequence[Sequence[float]]] = field(
        default_factory=dict,
    )
    riser_points: Mapping[str, Sequence[Sequence[float]]] = field(
        default_factory=dict,
    )
    surface_elevation: Sequence[Sequence[float]] | None = None
    case_id: str | None = None
    frame_index: int | None = None
    is_static: bool = False
    coordinate_system: CoordinateSystem = field(
        default_factory=CoordinateSystem,
    )

    def __post_init__(self) -> None:
        if not math.isfinite(self.time):
            raise ValueError("frame time must be finite")
        if self.frame_index is not None and self.frame_index < 0:
            raise ValueError("frame_index cannot be negative")
        body_poses = dict(self.body_poses)
        mooring_points = {
            key: _readonly_matrix(value)
            for key, value in self.mooring_points.items()
        }
        riser_points = {
            key: _readonly_matrix(value)
            for key, value in self.riser_points.items()
        }
        for points in (*mooring_points.values(), *riser_points.values()):
            if any(len(point) != 3 for point in points):
                raise ValueError("line point arrays must have shape (n, 3)")
        surface = self.surface_elevation
        if surface is not None:
            surface = _readonly_matrix(surface)
        object.__setattr__(self, "body_poses", body_poses)
        object.__setattr__(self, "mooring_points", mooring_points)
        object.__setattr__(self, "riser_points", riser_points)
        object.__setattr__(self, "surface_elevation", surface)

    def apply_to(self, model: SceneModel) -> SceneModel:
        """返回应用当前帧中物体和管线位置后的场景副本。"""

        if self.body_poses.keys() - model.body_geometries.keys():
            raise ValueError("frame contains a body absent from SceneModel")
        unknown_lines = (
            self.mooring_points.keys() | self.riser_points.keys()
        ) - model.cable_topologies.keys()
        if unknown_lines:
            raise ValueError("frame contains a cable absent from SceneModel")
        body_geometries = dict(model.body_geometries)
        for body_id, body_pose in self.body_poses.items():
            geometry = body_geometries[body_id]
            body_geometries[body_id] = BodyGeometryRef(
                resource_id=geometry.resource_id,
                pose=Pose(
                    position=Vector3(*body_pose.position),
                    rotation=EulerAngles(*body_pose.rotation),
                    coordinate_system=self.coordinate_system,
                ),
                vertex_count=geometry.vertex_count,
            )
        cable_topologies = dict(model.cable_topologies)
        for cable_id, points in {
            **self.mooring_points,
            **self.riser_points,
        }.items():
            topology = cable_topologies[cable_id]
            static_points = tuple(
                LinePoint(
                    arc_length=(
                        topology.points[index].arc_length
                        if index < len(topology.points)
                        else float(index)
                    ),
                    position=point,
                    point_id=(
                        topology.points[index].point_id
                        if index < len(topology.points)
                        else f"{cable_id}:{index}"
                    ),
                )
                for index, point in enumerate(points)
            )
            cable_topologies[cable_id] = CableTopology(
                cable_id=cable_id,
                points=static_points,
                cable_kind=topology.cable_kind,
            )
        return SceneModel(
            body_geometries=body_geometries,
            cable_topologies=cable_topologies,
            seabed_resource_id=model.seabed_resource_id,
            surface_shape=model.surface_shape,
            coordinate_system=model.coordinate_system,
            seabed_z=model.seabed_z,
            sea_surface_z=model.sea_surface_z,
        )


__all__ = [
    "AxisInfo",
    "AxisKind",
    "AxisSelection",
    "BodyGeometryRef",
    "BodyPose",
    "CableTopology",
    "CoordinateSystem",
    "CurveDomain",
    "CurveSeries",
    "EulerAngles",
    "FloatArray",
    "LinePoint",
    "MatrixData",
    "Pose",
    "ResultDataset",
    "SceneFrame",
    "SceneModel",
    "SliceSelection",
    "UnitSpec",
    "VariableInfo",
    "Vector3",
]
