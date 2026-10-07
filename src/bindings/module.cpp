#include "majiqwalk/core/engine.hpp"
#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
namespace py = pybind11;
using namespace majiqwalk;
using CArray = py::array_t<Complex, py::array::c_style | py::array::forcecast>;
using DArray = py::array_t<double, py::array::c_style | py::array::forcecast>;
template<class T> py::array_t<T> copy_array(const std::vector<T>& v, std::vector<py::ssize_t> shape) {
    py::array_t<T> result(shape);
    std::copy(v.begin(), v.end(), result.mutable_data());
    return result;
}
PYBIND11_MODULE(_core, m) {
    m.doc() = "MajiQwalK C++20 quantum and classical walk engines";
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

    py::class_<PersistentClassicalEngine>(m, "PersistentClassicalEngine")
        .def(py::init([](std::vector<std::size_t> shape, std::string boundary,
                         DArray transition_matrix, DArray initial_direction_state) {
            if (transition_matrix.ndim() != 2 || transition_matrix.shape(0) != transition_matrix.shape(1))
                throw std::invalid_argument("Persistent classical transition matrix must be a square 2D array");
            if (initial_direction_state.ndim() != 1)
                throw std::invalid_argument("Persistent classical initial directional state must be a flattened 1D array");
            std::vector<double> matrix(transition_matrix.data(),
                                       transition_matrix.data()+transition_matrix.size());
            std::vector<double> state(initial_direction_state.data(),
                                      initial_direction_state.data()+initial_direction_state.size());
            py::gil_scoped_release release;
            return std::make_unique<PersistentClassicalEngine>(
                std::move(shape), boundary, std::move(matrix), std::move(state));
        }), py::arg("shape"), py::arg("boundary"), py::arg("transition_matrix"),
            py::arg("initial_direction_state"))
        .def("advance", &PersistentClassicalEngine::advance, py::arg("steps")=1,
             py::call_guard<py::gil_scoped_release>())
        .def_property_readonly("step", &PersistentClassicalEngine::step)
        .def("norm", &PersistentClassicalEngine::norm, py::call_guard<py::gil_scoped_release>())
        .def("probability", [](const PersistentClassicalEngine& e) {
            std::vector<double> p;
            { py::gil_scoped_release release; p = e.probability(); }
            return copy_array(p, {static_cast<py::ssize_t>(p.size())});
        });

    py::class_<ClassicalEngine>(m, "ClassicalEngine")
        .def(py::init([](std::vector<std::size_t> shape, std::string boundary,
                         DArray step_probabilities, DArray initial_probability) {
            if (step_probabilities.ndim() != 1 || initial_probability.ndim() != 1)
                throw std::invalid_argument("Classical probabilities must be flattened 1D arrays");
            std::vector<double> weights(step_probabilities.data(),
                                        step_probabilities.data()+step_probabilities.size());
            std::vector<double> state(initial_probability.data(),
                                      initial_probability.data()+initial_probability.size());
            py::gil_scoped_release release;
            return std::make_unique<ClassicalEngine>(std::move(shape), boundary,
                                                      std::move(weights), std::move(state));
        }), py::arg("shape"), py::arg("boundary"), py::arg("step_probabilities"),
            py::arg("initial_probability"))
        .def("advance", &ClassicalEngine::advance, py::arg("steps")=1,
             py::call_guard<py::gil_scoped_release>())
        .def_property_readonly("step", &ClassicalEngine::step)
        .def("norm", &ClassicalEngine::norm, py::call_guard<py::gil_scoped_release>())
        .def("probability", [](const ClassicalEngine& e) {
            const auto& p = e.probability();
            return copy_array(p, {static_cast<py::ssize_t>(p.size())});
        });
}
