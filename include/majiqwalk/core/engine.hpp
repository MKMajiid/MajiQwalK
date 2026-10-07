#pragma once
#include <complex>
#include <cstddef>
#include <memory>
#include <span>
#include <string>
#include <variant>
#include <vector>

namespace majiqwalk {
using Complex = std::complex<double>;
enum class Boundary { Open, Periodic, Reflecting };

struct HilbertLayout {
    std::size_t sites;
    std::size_t coin_dimension;
    std::size_t dimension() const;
};
struct StateVector { std::vector<Complex> amplitudes; };
// Row-major, identical Hilbert indexing to StateVector. Dense evolution is a
// future capability; unsupported operations must fail, never convert silently.
struct DensityMatrix { std::vector<Complex> elements; HilbertLayout layout; };
using State = std::variant<StateVector, DensityMatrix>;

class CartesianGeometry {
public:
    CartesianGeometry(std::vector<std::size_t> shape, Boundary boundary);
    HilbertLayout layout() const { return layout_; }
    const std::vector<std::size_t>& shape() const { return shape_; }
    const std::vector<std::size_t>& destinations() const { return destinations_; }
    static constexpr std::size_t outside = static_cast<std::size_t>(-1);
private:
    std::vector<std::size_t> shape_, destinations_;
    HilbertLayout layout_{};
};

// Dispatch once per operation, never once per amplitude. Future split-step and
// time-dependent models assemble a different sequence using this same contract.
class Operation {
public:
    virtual ~Operation() = default;
    virtual void apply(StateVector& state, std::vector<Complex>& workspace,
                       std::size_t step) const = 0;
    virtual void apply(DensityMatrix&, std::vector<Complex>&, std::size_t) const;
};
class CoinOperation final : public Operation {
public:
    CoinOperation(HilbertLayout layout, std::vector<Complex> matrix, int threads);
    void apply(StateVector&, std::vector<Complex>&, std::size_t) const override;
private:
    HilbertLayout layout_;
    std::vector<Complex> matrix_;
    int threads_;
};
class ShiftOperation final : public Operation {
public:
    explicit ShiftOperation(const CartesianGeometry& geometry);
    void apply(StateVector&, std::vector<Complex>&, std::size_t) const override;
private:
    std::vector<std::size_t> destinations_;
};
struct EvolutionModel {
    std::vector<std::unique_ptr<Operation>> operations;
    void apply(State&, std::vector<Complex>&, std::size_t) const;
};

class ClassicalEngine {
public:
    ClassicalEngine(std::vector<std::size_t> shape, const std::string& boundary,
                    std::vector<double> step_probabilities,
                    std::vector<double> initial_probability);
    void advance(std::size_t steps = 1);
    const std::vector<double>& probability() const { return probability_; }
    double norm() const;
    std::size_t step() const { return step_; }
    std::size_t sites() const { return geometry_.layout().sites; }
private:
    CartesianGeometry geometry_;
    std::vector<double> step_probabilities_, probability_, workspace_;
    std::size_t step_ = 0;
};

class Engine {
public:
    Engine(std::vector<std::size_t> shape, const std::string& boundary,
           std::vector<Complex> coin, std::vector<Complex> initial_state,
           int threads = 1);
    void advance(std::size_t steps = 1);
    std::vector<double> probability() const;
    std::vector<Complex> reduced_coin() const;
    const std::vector<Complex>& amplitudes() const;
    double norm() const;
    std::size_t step() const { return step_; }
    HilbertLayout layout() const { return geometry_.layout(); }
private:
    CartesianGeometry geometry_;
    State state_;
    std::vector<Complex> workspace_;
    EvolutionModel model_;
    std::size_t step_ = 0;
};
bool openmp_enabled();
int max_threads();
} // namespace majiqwalk
