#include "majiqwalk/core/engine.hpp"
#include <cmath>
#include <iostream>
#include <stdexcept>
using namespace majiqwalk;
void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}
int main() {
    const double a = 1/std::sqrt(2.0);
    std::vector<Complex> coin{a,a,a,-a};
    std::vector<Complex> state(18);
    state[8] = a; state[9] = Complex(0,a);
    Engine e({9}, "open", coin, state);
    e.advance();
    auto p = e.probability();
    require(std::abs(p[3]-.5)<1e-14 && std::abs(p[5]-.5)<1e-14, "Hadamard one-step distribution");
    e.advance();
    p=e.probability();
    require(std::abs(p[2]-.25)<1e-14 && std::abs(p[4]-.5)<1e-14 && std::abs(p[6]-.25)<1e-14, "Hadamard two-step distribution");
    require(std::abs(e.norm()-1)<1e-14, "Unitary norm");
    for (auto boundary : {"periodic", "reflecting"}) {
        Engine bounded({9}, boundary, coin, state);
        bounded.advance(1000);
        require(std::abs(bounded.norm()-1)<1e-11, "Bounded walk norm");
    }
    bool rejected=false;
    try { Engine invalid({9}, "open", {1,1,1,1}, state); }
    catch (const std::invalid_argument&) { rejected=true; }
    require(rejected, "Nonunitary coin must fail in C++ too");

    std::vector<double> classical_state(9, 0.0);
    classical_state[4] = 1.0;
    ClassicalEngine classical({9}, "open", {0.5, 0.5}, classical_state);
    classical.advance(2);
    auto cp = classical.probability();
    require(std::abs(cp[2]-.25)<1e-14 && std::abs(cp[4]-.5)<1e-14 &&
            std::abs(cp[6]-.25)<1e-14, "Classical two-step binomial distribution");
    require(std::abs(classical.norm()-1)<1e-14, "Classical probability norm");
    bool bad_classical=false;
    try { ClassicalEngine invalid_classical({9}, "periodic", {0.4,0.4}, classical_state); }
    catch (const std::invalid_argument&) { bad_classical=true; }
    require(bad_classical, "Classical step probabilities must be stochastic");

    std::cout << "C++ scientific smoke tests passed\n";
}
