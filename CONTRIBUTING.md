# Contributing

Contributions to MajiQwalK are welcome.

Before opening a pull request, please describe the proposed change clearly, include tests for new or modified behavior, and update the relevant documentation or examples where appropriate.

For scientific features, please include enough information for another user to understand the implemented model and reproduce the result. Bug fixes should include a regression test whenever practical.

Run the project test suite before submitting changes:

```bash
python -m pytest -q
cmake -S . -B build/cpp -DMAJIQWALK_BUILD_PYTHON=OFF -DMAJIQWALK_BUILD_TESTS=ON
cmake --build build/cpp --config Release
ctest --test-dir build/cpp -C Release --output-on-failure
```

Please keep changes focused and maintain backward compatibility where practical. If a change affects configuration or stored output, document it clearly in the pull request.
