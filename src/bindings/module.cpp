#include "majiqwalk/core/engine.hpp"
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;
using namespace majiqwalk;
using CArray = py::array_t<Complex, py::array::c_style | py::array::forcecast>;
template<class T> py::array_t<T> copy_array(const std::vector<T>& v, std::vector<py::ssize_t> shape) {
    py::array_t<T> result(shape);
    std::copy(v.begin(), v.end(), result.mutable_data());
    return result;
}
PYBIND11_MODULE(_core, m) {
    m.doc() = "MajiQwalK C++20 state-vector engine";
    m.def("openmp_enabled", &openmp_enabled);
    m.def("max_threads", &max_threads);
    py::class_<Engine>(m, "Engine")
        .def(py::init([](std::vector<std::size_t> shape, std::string boundary,
                         CArray coin, CArray state, int threads) {
            if (coin.ndim() != 2 || coin.shape(0) != coin.shape(1))
                throw std::invalid_argument("Coin must be a square 2D array");
            if (state.ndim() != 1)
                throw std::invalid_argument("Initial state must be a flattened 1D array");
            std::vector<Complex> c(coin.data(), coin.data()+coin.size());
            std::vector<Complex> s(state.data(), state.data()+state.size());
            py::gil_scoped_release release;
            return std::make_unique<Engine>(std::move(shape), boundary, std::move(c), std::move(s), threads);
        }), py::arg("shape"), py::arg("boundary"), py::arg("coin"), py::arg("initial_state"), py::arg("threads")=1)
        .def("advance", &Engine::advance, py::arg("steps")=1, py::call_guard<py::gil_scoped_release>())
        .def_property_readonly("step", &Engine::step)
        .def("norm", &Engine::norm, py::call_guard<py::gil_scoped_release>())
        .def("probability", [](const Engine& e) {
            std::vector<double> p;
            { py::gil_scoped_release release; p = e.probability(); }
            return copy_array(p, {static_cast<py::ssize_t>(p.size())});
        })
        .def("state", [](const Engine& e) {
            auto l = e.layout();
            return copy_array(e.amplitudes(), {static_cast<py::ssize_t>(l.sites), static_cast<py::ssize_t>(l.coin_dimension)});
        })
        .def("reduced_coin", [](const Engine& e) {
            std::vector<Complex> rho;
            { py::gil_scoped_release release; rho = e.reduced_coin(); }
            auto d = static_cast<py::ssize_t>(e.layout().coin_dimension);
            return copy_array(rho, {d,d});
        });
}
