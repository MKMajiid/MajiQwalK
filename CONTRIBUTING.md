# Contributing

Every new physics feature should state its evolution equation, basis and
parameter conventions, reference, reproducible configuration and an independent
validation. Test normalization and edge behavior. Avoid introducing dense global
walk matrices in production kernels.

Run the checks in README before proposing a change. Keep schema-v1 names stable;
add compatible optional fields or introduce a new schema version for breaking
changes. Regenerate `schemas/config-v1.json` after changing configuration models.

Development versions are not automatically stable releases. Do not claim a
feature is supported solely because an interface or roadmap entry exists.
