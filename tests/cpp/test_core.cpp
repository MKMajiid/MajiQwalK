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
    std::cout << "C++ scientific smoke tests passed\n";
}
