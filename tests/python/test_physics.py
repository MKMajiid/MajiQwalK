import numpy as np
import pytest
from majiqwalk import _core

def random_unitary(d, seed):
    rng=np.random.default_rng(seed)
    return np.linalg.qr(rng.normal(size=(d,d))+1j*rng.normal(size=(d,d)))[0]

def dense_shift(shape, boundary):
    """Independent small-system matrix reference, no production shift routines."""
    sites, d = int(np.prod(shape)), 2*len(shape)
    shift=np.zeros((sites*d,sites*d),complex)
    for coordinate in np.ndindex(*shape):
        site=np.ravel_multi_index(coordinate,shape)
        for axis in range(len(shape)):
            for sign, displacement in enumerate([-1,1]):
                port=2*axis+sign
                target=list(coordinate); target[axis]+=displacement; new_port=port
                if not 0<=target[axis]<shape[axis]:
                    if boundary=="periodic": target[axis]%=shape[axis]
                    else: target=list(coordinate); new_port=port^1
                out=np.ravel_multi_index(tuple(target),shape)*d+new_port
                shift[out,site*d+port]=1
    return shift

@pytest.mark.parametrize("shape", [[5],[3,4],[2,3,2],[1],[1,2]])
@pytest.mark.parametrize("boundary", ["periodic","reflecting"])
def test_against_dense_global_unitary(shape,boundary):
    sites,d=int(np.prod(shape)),2*len(shape)
    coin=random_unitary(d,7)
    rng=np.random.default_rng(12)
    initial=rng.normal(size=sites*d)+1j*rng.normal(size=sites*d)
    initial/=np.linalg.norm(initial)
    shift=dense_shift(shape,boundary)
    np.testing.assert_allclose(shift.conj().T@shift,np.eye(sites*d))
    unitary=shift@np.kron(np.eye(sites),coin)
    reference=initial.copy()
    engine=_core.Engine(shape,boundary,coin,initial)
    for step in range(7):
        np.testing.assert_allclose(engine.state().reshape(-1),reference,atol=2e-14,rtol=0)
        matrix=reference.reshape(sites,d)
        np.testing.assert_allclose(engine.reduced_coin(),matrix.T@matrix.conj(),atol=2e-14,rtol=0)
        np.testing.assert_allclose(engine.probability(),np.sum(abs(matrix)**2,axis=1),atol=2e-14)
        assert abs(engine.norm()-1)<2e-14
        reference=unitary@reference
        engine.advance()

def test_hadamard_exact_and_ballistic_limit():
    n=1201; a=1/np.sqrt(2); coin=np.array([[a,a],[a,-a]])
    state=np.zeros(n*2,complex); state[1200:1202]=[a,1j*a]
    engine=_core.Engine([n],"open",coin,state); engine.advance(2)
    p=engine.probability()
    np.testing.assert_allclose(p[[598,600,602]],[.25,.5,.25],atol=1e-14)
    engine.advance(498); p=engine.probability(); x=np.arange(n)-n//2
    np.testing.assert_allclose(p,p[::-1],atol=1e-14)
    assert abs(p@x)<1e-11
    assert p[(x-500)%2!=0].sum()==0
    assert abs((p@x**2)/500**2-(1-1/np.sqrt(2)))<2e-4

def test_open_window_rejects_leakage():
    with pytest.raises(RuntimeError,match="open window"):
        engine=_core.Engine([1],"open",np.eye(2),np.array([1,0],complex)); engine.advance()

@pytest.mark.parametrize("coin,state", [(np.ones((2,2)),[1,0]),(np.eye(2),[1,1]),(np.eye(2),[np.nan,0])])
def test_cpp_revalidates_inputs(coin,state):
    with pytest.raises(ValueError):
        _core.Engine([1],"periodic",coin,np.array(state,complex))

def test_openmp_matches_serial():
    if not _core.openmp_enabled(): pytest.skip("OpenMP unavailable")
    coin=random_unitary(2,5)
    state=np.zeros(8192,complex); state[4096]=1
    serial=_core.Engine([4096],"periodic",coin,state,1)
    parallel=_core.Engine([4096],"periodic",coin,state,2)
    serial.advance(12); parallel.advance(12)
    np.testing.assert_array_equal(serial.state(),parallel.state())


@pytest.mark.parametrize("dimension", [2, 4, 6])
def test_identity_coin_is_dimension_independent(dimension):
    from majiqwalk.config import CoinSpec
    np.testing.assert_array_equal(CoinSpec(type="identity").array(dimension), np.eye(dimension))

@pytest.mark.parametrize("dimension", [4, 6])
def test_dft_coin_is_unitary_for_square_and_cubic_port_counts(dimension):
    from majiqwalk.config import CoinSpec
    coin = CoinSpec(type="dft").array(dimension)
    np.testing.assert_allclose(coin.conj().T @ coin, np.eye(dimension), atol=1e-12, rtol=0)


def test_classical_simulation_hdf5_pipeline(tmp_path):
    import h5py
    from majiqwalk import Config, Simulation
    config = Config.model_validate({
        "simulation": {"steps": 20, "save_every": 2},
        "model": {"type": "classical_random_walk"},
        "geometry": {"type": "line", "shape": [41], "boundary": "open"},
        "classical": {"step_probabilities": [0.5, 0.5]},
        "initial_state": {"position": {"site": 20}},
        "observables": [{"type": "probability"}, {"type": "moments"}],
        "output": {"file": "ignored.h5"},
    })
    target = tmp_path / "classical.h5"
    result = Simulation(config).run(target)
    np.testing.assert_array_equal(result.steps, np.arange(0, 21, 2))
    with h5py.File(target, "r") as file:
        assert file["metadata"].attrs["model_type"] == "classical_random_walk"
        assert file["metadata"].attrs["representation"] == "probability"
        np.testing.assert_allclose(file["model/step_probabilities"][()], [0.5, 0.5])
        final = file["observables/probability"][-1]
        x = np.arange(41) - 20
        assert abs(final.sum() - 1.0) < 2e-14
        assert abs(final @ (x**2) - 20.0) < 2e-12
        assert "observables/entanglement" not in file


def test_quantum_classical_compare_pipeline(tmp_path):
    from majiqwalk import Config, Simulation
    from majiqwalk.analysis import compare_transport
    from majiqwalk.plot import plot_comparison

    base = {
        "simulation": {"steps": 20, "save_every": 1},
        "geometry": {"type": "line", "shape": [41], "boundary": "open"},
        "initial_state": {"position": {"site": 20}},
        "observables": [{"type": "probability"}, {"type": "moments"}],
    }
    classical = Config.model_validate({
        **base,
        "model": {"type": "classical_random_walk"},
        "output": {"file": "memoryless.h5"},
    })
    persistent = Config.model_validate({
        **base,
        "model": {"type": "classical_random_walk"},
        "classical": {"type": "persistent", "persistence": 0.8},
        "output": {"file": "persistent.h5"},
    })
    first = tmp_path / "memoryless.h5"
    second = tmp_path / "persistent.h5"
    Simulation(classical).run(first)
    Simulation(persistent).run(second)
    comparison = compare_transport(first, second)
    np.testing.assert_array_equal(comparison["steps"], np.arange(21))
    outputs = plot_comparison(first, second, tmp_path / "figures", ["png"])
    assert {path.name for path in outputs} == {
        "probability_comparison_t20.png",
        "transport_variance_comparison.png",
        "transport_rms_comparison.png",
    }
    assert all(path.stat().st_size > 0 for path in outputs)
