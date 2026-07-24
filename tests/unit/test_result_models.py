"""Contract tests for result and scene data models."""

import pytest

from core.models.result import (
    AxisInfo,
    AxisSelection,
    BodyGeometryRef,
    BodyPose,
    CableTopology,
    CoordinateSystem,
    CurveSeries,
    EulerAngles,
    LinePoint,
    MatrixData,
    Pose,
    ResultDataset,
    SceneFrame,
    SceneModel,
    SliceSelection,
    VariableInfo,
    Vector3,
)


def axis(
    key: str,
    values: tuple[float, ...],
    kind: str,
    unit: str,
) -> AxisInfo:
    return AxisInfo(
        axis_key=key,
        values=values,
        kind=kind,  # type: ignore[arg-type]
        unit=unit,
    )


def test_axis_and_dataset_keep_explicit_dimensions() -> None:
    time = axis("time", (0.0, 0.5, 1.0), "time", "s")
    frequency = axis("frequency", (0.1, 0.2), "frequency", "Hz")
    dataset = ResultDataset(
        dataset_id="body-displacement",
        case_id="case-001",
        source_resource_id="output/body",
        axes=(time, frequency),
        variables=(VariableInfo("surge", "m"),),
        result_kind="body",
    )

    assert dataset.axis("time") is time
    assert dataset.variable("surge").unit == "m"
    assert dataset.axis("frequency").size == 2


@pytest.mark.parametrize(
    ("kind", "x"),
    [
        ("time", (0.0, 1.0)),
        ("frequency", (0.1, 0.2)),
        ("arc_length", (0.0, 10.0)),
    ],
)
def test_curve_series_supports_time_frequency_and_arc_length(
    kind: str,
    x: tuple[float, ...],
) -> None:
    series = CurveSeries(
        x=x,
        y=(1.0, 2.0),
        x_label=kind,
        y_label="surge",
        x_unit="s" if kind == "time" else None,
        y_unit="m",
        domain=kind,  # type: ignore[arg-type]
    )

    assert series.point_count == 2
    assert series.domain == kind
    assert isinstance(series.x, tuple)
    assert isinstance(series.y, tuple)


def test_curve_rejects_mismatched_lengths_and_negative_arc_length() -> None:
    with pytest.raises(ValueError, match="same length"):
        CurveSeries(
            x=(0.0,),
            y=(1.0, 2.0),
            x_label="time",
            y_label="value",
        )

    with pytest.raises(ValueError, match="non-negative"):
        CurveSeries(
            x=(-1.0,),
            y=(1.0,),
            x_label="arc length",
            y_label="value",
            domain="arc_length",
        )


def test_matrix_keeps_row_column_labels_and_shape() -> None:
    matrix = MatrixData(
        row_labels=("surge", "sway"),
        column_labels=("0 deg", "90 deg"),
        values=((1.0, 2.0), (3.0, 4.0)),
        unit="m",
    )

    assert matrix.shape == (2, 2)
    assert isinstance(matrix.values, tuple)

    with pytest.raises(ValueError, match="shape"):
        MatrixData(
            row_labels=("surge",),
            column_labels=("0 deg", "90 deg"),
            values=((1.0,),),
        )


def test_selection_rejects_ambiguous_or_overlapping_axes() -> None:
    with pytest.raises(ValueError, match="index or value"):
        AxisSelection("time")
    with pytest.raises(ValueError, match="not both"):
        AxisSelection("time", index=0, value=0.0)
    with pytest.raises(ValueError, match="varying and fixed"):
        SliceSelection(
            varying_axes=("time",),
            fixed_axes=(AxisSelection("time", index=0),),
        )


def test_scene_model_and_frame_combine_static_and_dynamic_state() -> None:
    body = BodyGeometryRef(
        resource_id="body.stl",
        pose=Pose(
            position=Vector3(0.0, 0.0, 10.0),
            rotation=EulerAngles(),
        ),
    )
    mooring = CableTopology(
        cable_id="mooring-1",
        cable_kind="mooring",
        points=(
            LinePoint(arc_length=0.0, position=(0.0, 0.0, 10.0)),
            LinePoint(arc_length=100.0, position=(10.0, 0.0, -90.0)),
        ),
    )
    model = SceneModel(
        body_geometries={"body-1": body},
        cable_topologies={"mooring-1": mooring},
        seabed_resource_id="seabed.obj",
        surface_shape=(8, 8),
        coordinate_system=CoordinateSystem(name="global", length_unit="m"),
    )
    frame = SceneFrame(
        time=5.0,
        frame_index=10,
        case_id="case-001",
        body_poses={
            "body-1": BodyPose(
                position=(1.0, 2.0, 11.0),
                rotation=(0.0, 0.0, 5.0),
            ),
        },
        mooring_points={
            "mooring-1": ((1.0, 2.0, 11.0), (11.0, 2.0, -89.0)),
        },
    )

    assert model.body_ids == ("body-1",)
    assert len(frame.mooring_points["mooring-1"]) == 2
    assert isinstance(frame.mooring_points["mooring-1"], tuple)

    moved = frame.apply_to(model)
    assert moved.body_geometries["body-1"].pose.position == Vector3(
        1.0,
        2.0,
        11.0,
    )
    assert moved.cable_topologies["mooring-1"].points[1].arc_length == 100.0


def test_scene_frame_rejects_unknown_geometry_and_bad_line_shape() -> None:
    model = SceneModel()
    unknown_frame = SceneFrame(
        time=0.0,
        body_poses={
            "missing": BodyPose(
                position=(0.0, 0.0, 0.0),
                rotation=(0.0, 0.0, 0.0),
            ),
        },
    )
    with pytest.raises(ValueError, match="absent from SceneModel"):
        unknown_frame.apply_to(model)

    with pytest.raises(ValueError, match="shape"):
        SceneFrame(time=0.0, mooring_points={"line": ((0.0, 0.0), (0.0, 0.0))})
