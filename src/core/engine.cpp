#include "majiqwalk/core/engine.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace majiqwalk {
namespace {
std::size_t checked_product(std::size_t a, std::size_t b) {
    if (b != 0 && a > std::numeric_limits<std::size_t>::max() / b)
        throw std::overflow_error("Hilbert-space dimension overflows size_t");
    return a * b;
}
Boundary parse_boundary(const std::string& s) {
    if (s == "open") return Boundary::Open;
    if (s == "periodic") return Boundary::Periodic;
    if (s == "reflecting") return Boundary::Reflecting;
    throw std::invalid_argument("Unknown boundary: " + s);
}
bool finite(Complex z) { return std::isfinite(z.real()) && std::isfinite(z.imag()); }
}
std::size_t HilbertLayout::dimension() const {
    return checked_product(sites, coin_dimension);
}
CartesianGeometry::CartesianGeometry(std::vector<std::size_t> shape, Boundary boundary)
    : shape_(std::move(shape)) {
    if (shape_.empty() || shape_.size() > 3)
        throw std::invalid_argument("Cartesian dimension must be 1, 2 or 3");
    layout_ = {1, 2 * shape_.size()};
    for (auto n : shape_) {
        if (n < 1) throw std::invalid_argument("All shape entries must be positive");
        layout_.sites = checked_product(layout_.sites, n);
    }
    destinations_.resize(layout_.dimension());
    for (std::size_t site = 0; site < layout_.sites; ++site) {
        std::size_t stride = layout_.sites;
        for (std::size_t axis = 0; axis < shape_.size(); ++axis) {
            stride /= shape_[axis];
            auto coordinate = (site / stride) % shape_[axis];
            for (std::size_t sign = 0; sign < 2; ++sign) {
                auto port = 2 * axis + sign;
                bool outbound = (sign == 0 && coordinate == 0) ||
                                (sign == 1 && coordinate == shape_[axis] - 1);
                auto i = site * layout_.coin_dimension + port;
                if (!outbound) {
                    auto target = sign == 0 ? site - stride : site + stride;
                    destinations_[i] = target * layout_.coin_dimension + port;
                } else if (boundary == Boundary::Periodic) {
                    auto displacement = (shape_[axis] - 1) * stride;
                    auto target = sign == 0 ? site + displacement : site - displacement;
                    destinations_[i] = target * layout_.coin_dimension + port;
                } else if (boundary == Boundary::Reflecting) {
                    destinations_[i] = site * layout_.coin_dimension + (port ^ 1);
                } else {
                    destinations_[i] = outside;
                }
            }
        }
    }
}
void Operation::apply(DensityMatrix&, std::vector<Complex>&, std::size_t) const {
    throw std::logic_error("Density-matrix evolution is not implemented in this milestone");
}
CoinOperation::CoinOperation(HilbertLayout layout, std::vector<Complex> matrix, int threads)
    : layout_(layout), matrix_(std::move(matrix)), threads_(threads) {
    auto d = layout_.coin_dimension;
    if (layout_.sites > static_cast<std::size_t>(std::numeric_limits<std::ptrdiff_t>::max()))
        throw std::overflow_error("Site count exceeds the signed OpenMP loop range");
    if (matrix_.size() != checked_product(d, d))
        throw std::invalid_argument("Coin matrix shape does not match the port count");
    if (threads_ < 1) throw std::invalid_argument("threads must be positive");
    if (!openmp_enabled() && threads_ > 1)
        throw std::invalid_argument("This build has no OpenMP: use threads=1");
    for (auto z : matrix_) if (!finite(z)) throw std::invalid_argument("Non-finite coin");
    for (std::size_t a = 0; a < d; ++a) for (std::size_t b = 0; b < d; ++b) {
        Complex inner{};
        for (std::size_t k = 0; k < d; ++k) inner += std::conj(matrix_[k*d+a]) * matrix_[k*d+b];
        if (std::abs(inner - Complex(a == b ? 1.0 : 0.0)) > 1e-12)
            throw std::invalid_argument("Coin must be unitary (tolerance 1e-12)");
    }
}
void CoinOperation::apply(StateVector& state, std::vector<Complex>& workspace, std::size_t) const {
    auto d = layout_.coin_dimension;
    if (state.amplitudes.size() != layout_.dimension() || workspace.size() != layout_.dimension())
        throw std::invalid_argument("State/workspace shape does not match HilbertLayout");
    const auto site_count = static_cast<std::ptrdiff_t>(layout_.sites);
#ifdef _OPENMP
#pragma omp parallel for num_threads(threads_) if(layout_.sites >= 4096 && threads_ > 1)
#endif
    // MSVC's OpenMP implementation requires a signed canonical loop index.
    for (std::ptrdiff_t index = 0; index < site_count; ++index) {
        const auto site = static_cast<std::size_t>(index);
        for (std::size_t a = 0; a < d; ++a) {
            Complex z{};
            for (std::size_t b = 0; b < d; ++b)
                z += matrix_[a*d+b] * state.amplitudes[site*d+b];
            workspace[site*d+a] = z;
        }
    }
    state.amplitudes.swap(workspace);
}
ShiftOperation::ShiftOperation(const CartesianGeometry& geometry)
    : destinations_(geometry.destinations()) {}
void ShiftOperation::apply(StateVector& state, std::vector<Complex>& workspace, std::size_t) const {
    if (state.amplitudes.size() != destinations_.size() || workspace.size() != destinations_.size())
        throw std::invalid_argument("Shift state/workspace size mismatch");
    // Validate before changing any destination. Open is an infinite-lattice
    // window, not an absorbing boundary. Never silently discard probability.
    for (std::size_t i = 0; i < destinations_.size(); ++i)
        if (destinations_[i] == CartesianGeometry::outside && state.amplitudes[i] != Complex{})
            throw std::runtime_error("Walk reached the open window edge; enlarge geometry.shape or choose an explicit boundary");
    std::fill(workspace.begin(), workspace.end(), Complex{});
    for (std::size_t i = 0; i < destinations_.size(); ++i)
        if (destinations_[i] != CartesianGeometry::outside)
            workspace[destinations_[i]] = state.amplitudes[i];
    state.amplitudes.swap(workspace);
}
void EvolutionModel::apply(State& state, std::vector<Complex>& workspace, std::size_t step) const {
    for (const auto& operation : operations)
        std::visit([&](auto& s) { operation->apply(s, workspace, step); }, state);
}
Engine::Engine(std::vector<std::size_t> shape, const std::string& boundary,
               std::vector<Complex> coin, std::vector<Complex> initial_state, int threads)
    : geometry_(std::move(shape), parse_boundary(boundary)),
      state_(StateVector{std::move(initial_state)}), workspace_(geometry_.layout().dimension()) {
    if (amplitudes().size() != layout().dimension())
        throw std::invalid_argument("Initial state dimension does not match geometry");
    for (auto z : amplitudes()) if (!finite(z)) throw std::invalid_argument("Non-finite initial state");
    if (std::abs(norm() - 1.0) > 1e-12)
        throw std::invalid_argument("Initial state must be normalized (tolerance 1e-12)");
    model_.operations.push_back(std::make_unique<CoinOperation>(layout(), std::move(coin), threads));
    model_.operations.push_back(std::make_unique<ShiftOperation>(geometry_));
}
void Engine::advance(std::size_t steps) {
    for (std::size_t i = 0; i < steps; ++i) {
        model_.apply(state_, workspace_, step_);
        ++step_;
    }
}
const std::vector<Complex>& Engine::amplitudes() const {
    return std::get<StateVector>(state_).amplitudes;
}
double Engine::norm() const {
    double total = 0.0;
    for (auto z : amplitudes()) total += std::norm(z);
    return total;
}
std::vector<double> Engine::probability() const {
    auto l = layout();
    std::vector<double> p(l.sites, 0.0);
    for (std::size_t x = 0; x < l.sites; ++x)
        for (std::size_t c = 0; c < l.coin_dimension; ++c)
            p[x] += std::norm(amplitudes()[x*l.coin_dimension+c]);
    return p;
}
std::vector<Complex> Engine::reduced_coin() const {
    auto l = layout();
    std::vector<Complex> rho(l.coin_dimension*l.coin_dimension, 0.0);
    for (std::size_t x = 0; x < l.sites; ++x)
        for (std::size_t a = 0; a < l.coin_dimension; ++a)
            for (std::size_t b = 0; b < l.coin_dimension; ++b)
                rho[a*l.coin_dimension+b] += amplitudes()[x*l.coin_dimension+a] *
                    std::conj(amplitudes()[x*l.coin_dimension+b]);
    return rho;
}
bool openmp_enabled() {
#ifdef _OPENMP
    return true;
#else
    return false;
#endif
}
int max_threads() {
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}
} // namespace majiqwalk
