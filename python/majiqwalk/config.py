"""Schema-v1 configuration, numerical validation, and coin/state construction."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
import yaml

TOL = 1e-12
Pair = list[float]


class Spec(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


def complex_values(values, name):
    array = np.asarray(values, dtype=float)
    if array.ndim < 2 or array.shape[-1] != 2 or not np.isfinite(array).all():
        raise ValueError(f"{name}: complex numbers must be finite [real, imaginary] pairs")
    return array[..., 0] + 1j * array[..., 1]


class SimulationSpec(Spec):
    steps: int = Field(default=100, ge=0)
    save_every: int = Field(default=1, ge=1)
    representation: Literal["state_vector", "density_matrix"] = "state_vector"
    max_memory_mib: int = Field(default=512, ge=1)


class GeometrySpec(Spec):
    type: Literal["line", "square", "cubic"] = "line"
    shape: list[int] | None = None
    sites: int | None = Field(default=None, ge=1)
    boundary: Literal["open", "periodic", "reflecting"] = "open"
    origin: list[float] | None = None

    @model_validator(mode="after")
    def validate_geometry(self):
        ndim = {"line": 1, "square": 2, "cubic": 3}[self.type]
        if self.sites is not None:
            if ndim != 1 or self.shape is not None:
                raise ValueError("geometry.sites is a line-only alias; do not combine with shape")
            self.shape = [self.sites]
            self.sites = None
        if self.shape is None or len(self.shape) != ndim or any(n < 1 for n in self.shape):
            raise ValueError(f"geometry.shape must contain {ndim} positive integer(s)")
        if self.origin is None:
            self.origin = [float(n // 2) for n in self.shape]
        if len(self.origin) != ndim or not np.isfinite(self.origin).all():
            raise ValueError("geometry.origin must contain one finite number per axis")
        return self


class ModelSpec(Spec):
    type: Literal["coined"] = "coined"


class CoinSpec(Spec):
    type: Literal["hadamard", "custom", "u2", "grover", "dft", "identity"] = "hadamard"
    dimension: int | None = Field(default=None, ge=1)
    matrix: list[list[Pair]] | None = None
    theta: float = 0.0
    phi: float = 0.0
    lam: float = 0.0
    global_phase: float = 0.0

    def array(self, dimension):
        if self.dimension is not None and self.dimension != dimension:
            raise ValueError(f"coin.dimension must equal the {dimension} geometry ports")
        if self.matrix is not None and self.type != "custom":
            raise ValueError("coin.matrix requires coin.type: custom")
        if self.type != "u2" and any(angle != 0 for angle in (self.theta, self.phi, self.lam)):
            raise ValueError("coin.theta, coin.phi and coin.lam are parameters of the u2 coin only")
        if not np.isfinite([self.theta, self.phi, self.lam, self.global_phase]).all():
            raise ValueError("coin parameters must be finite")
        if self.type == "custom":
            if self.matrix is None:
                raise ValueError("coin.matrix is required for a custom coin")
            c = complex_values(self.matrix, "coin.matrix")
        elif self.type == "hadamard":
            if dimension != 2:
                raise ValueError("Hadamard coin has 2 ports; use grover, dft, identity, or custom in 2D/3D")
            c = np.array([[1, 1], [1, -1]], dtype=complex) / math.sqrt(2)
        elif self.type == "u2":
            if dimension != 2:
                raise ValueError("u2 coin requires a two-port geometry")
            a, b = math.cos(self.theta / 2), math.sin(self.theta / 2)
            c = np.array([[a, -np.exp(1j*self.lam)*b],
                          [np.exp(1j*self.phi)*b, np.exp(1j*(self.phi+self.lam))*a]])
        elif self.type == "grover":
            c = 2 * np.ones((dimension, dimension)) / dimension - np.eye(dimension)
        elif self.type == "dft":
            k = np.arange(dimension)
            c = np.exp(2j*np.pi*np.outer(k, k)/dimension)/math.sqrt(dimension)
        elif self.type == "identity":
            c = np.eye(dimension, dtype=complex)
        else:
            raise ValueError(f"Unsupported coin type: {self.type}")
        c = np.asarray(c, dtype=np.complex128) * np.exp(1j*self.global_phase)
        if c.shape != (dimension, dimension):
            raise ValueError(f"coin.matrix expected {dimension} x {dimension}; received {c.shape}")
        if not np.allclose(c.conj().T @ c, np.eye(dimension), atol=TOL, rtol=0):
            raise ValueError("coin.matrix must be unitary (absolute tolerance 1e-12)")
        return c


class PositionSpec(Spec):
    site: int | None = Field(default=None, ge=0)
    amplitudes: list[Pair] | None = None


class InitialCoinSpec(Spec):
    basis: int | None = Field(default=None, ge=0)
    amplitudes: list[Pair] | None = None


class InitialStateSpec(Spec):
    position: PositionSpec | None = None
    coin: InitialCoinSpec | None = None
    amplitudes: list[Pair] | None = None

    @model_validator(mode="after")
    def exclusive(self):
        if self.amplitudes is not None and (self.position is not None or self.coin is not None):
            raise ValueError("Use either a full initial state or separate position and coin states")
        if self.position and self.position.site is not None and self.position.amplitudes is not None:
            raise ValueError("initial_state.position: use site or amplitudes")
        if self.coin and self.coin.basis is not None and self.coin.amplitudes is not None:
            raise ValueError("initial_state.coin: use basis or amplitudes")
        return self

    def validate_dimensions(self, shape, dimension):
        sites = math.prod(shape)
        for values, n, name in [
            (self.amplitudes, sites*dimension, "initial_state.amplitudes"),
            (self.position.amplitudes if self.position else None, sites, "initial_state.position.amplitudes"),
            (self.coin.amplitudes if self.coin else None, dimension, "initial_state.coin.amplitudes"),
        ]:
            if values is not None:
                v = complex_values(values, name)
                if v.shape != (n,) or abs(np.vdot(v, v).real - 1) > TOL:
                    raise ValueError(f"{name} must contain {n} amplitudes with squared norm 1")
        if self.position and self.position.site is not None and self.position.site >= sites:
            raise ValueError("initial_state.position.site is outside the geometry")
        if self.coin and self.coin.basis is not None and self.coin.basis >= dimension:
            raise ValueError("initial_state.coin.basis is outside the coin space")

    def array(self, shape, dimension):
        if self.amplitudes is not None:
            return complex_values(self.amplitudes, "initial_state.amplitudes").reshape(-1)
        sites = math.prod(shape)
        position = self.position or PositionSpec()
        coin = self.coin or InitialCoinSpec()
        if position.amplitudes is not None:
            p = complex_values(position.amplitudes, "initial_state.position.amplitudes")
        else:
            site = position.site
            if site is None:
                site = np.ravel_multi_index(tuple(n//2 for n in shape), tuple(shape))
            p = np.zeros(sites, dtype=complex)
            p[site] = 1
        if coin.amplitudes is not None:
            c = complex_values(coin.amplitudes, "initial_state.coin.amplitudes")
        else:
            c = np.zeros(dimension, dtype=complex)
            c[coin.basis or 0] = 1
        return np.outer(p, c).reshape(-1)


class BackendSpec(Spec):
    type: Literal["cpu"] = "cpu"
    threads: int | Literal["auto"] = "auto"

    @model_validator(mode="after")
    def positive(self):
        if isinstance(self.threads, int) and self.threads < 1:
            raise ValueError("backend.threads must be positive or auto")
        return self


class ObservableSpec(Spec):
    type: Literal["probability", "moments", "coin_position_entanglement", "time_average_probability"]
    orders: list[int] | None = None

    @model_validator(mode="after")
    def validate_orders(self):
        if self.type == "moments":
            if self.orders is None:
                self.orders = [1, 2]
            if not self.orders or len(set(self.orders)) != len(self.orders) or any(n < 1 or n > 4 for n in self.orders):
                raise ValueError("moments.orders must contain unique integers from 1 to 4")
        elif self.orders is not None:
            raise ValueError("orders is only valid for the moments observable")
        return self


class OutputSpec(Spec):
    file: str = "results.h5"
    save_state: bool = False
    overwrite: bool = False


class PlotSpec(Spec):
    preset: Literal["aps_pr"] = "aps_pr"
    formats: list[Literal["pdf", "svg", "png"]] = Field(default_factory=lambda: ["pdf", "png"])


class Config(Spec):
    schema_version: Literal[1] = 1
    simulation: SimulationSpec = Field(default_factory=SimulationSpec)
    geometry: GeometrySpec
    model: ModelSpec = Field(default_factory=ModelSpec)
    coin: CoinSpec = Field(default_factory=CoinSpec)
    initial_state: InitialStateSpec = Field(default_factory=InitialStateSpec)
    backend: BackendSpec = Field(default_factory=BackendSpec)
    observables: list[ObservableSpec] = Field(default_factory=lambda: [
        ObservableSpec(type="probability"), ObservableSpec(type="moments"),
        ObservableSpec(type="coin_position_entanglement")])
    output: OutputSpec = Field(default_factory=OutputSpec)
    plot: PlotSpec = Field(default_factory=PlotSpec)

    @field_validator("schema_version", mode="before")
    @classmethod
    def integer_version(cls, value):
        if type(value) is not int:
            raise ValueError("schema_version must be an integer")
        return value

    @model_validator(mode="after")
    def validate_physics(self):
        shape = self.geometry.shape
        dimension = 2 * len(shape)
        self.coin.array(dimension)
        self.initial_state.validate_dimensions(shape, dimension)
        kinds = [o.type for o in self.observables]
        if not kinds or len(kinds) != len(set(kinds)):
            raise ValueError("observables must be a nonempty list of distinct types")
        if not self.output.file.strip():
            raise ValueError("output.file cannot be empty")
        return self

    def to_yaml(self):
        return yaml.safe_dump(self.model_dump(exclude_none=True), sort_keys=False)

    @classmethod
    def from_yaml(cls, path):
        with Path(path).open(encoding="utf-8") as stream:
            value = yaml.load(stream, Loader=_UniqueSafeLoader)
        if not isinstance(value, dict):
            raise ValueError("Configuration must be a YAML mapping")
        return cls.model_validate(value)


class _UniqueSafeLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML configuration keys must be strings")
        if key in mapping:
            raise ValueError(f"Duplicate YAML key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)
