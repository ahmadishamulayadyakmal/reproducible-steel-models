# Reproducible development/test environment.
# Build:  docker build -t metallurgy-portfolio .
# Tests:  docker run --rm metallurgy-portfolio python -m pytest
#         docker run --rm metallurgy-portfolio fpm test
FROM mambaorg/micromamba:1.5.8

USER root
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml \
    && micromamba clean --all --yes

WORKDIR /workspace
COPY --chown=$MAMBA_USER:$MAMBA_USER . .

USER $MAMBA_USER
RUN python -m pip install --no-deps -e .

# Fail the image build if either test suite is broken.
RUN python -m pytest && fpm test

CMD ["/bin/bash"]
