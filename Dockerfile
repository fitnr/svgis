FROM ghcr.io/osgeo/gdal:ubuntu-small-latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY ["Makefile", "Makefile"]

COPY ["README.md", "README.md"]

COPY ["pyproject.toml", "pyproject.toml"]

COPY ["./src", "src/"]

RUN ["python", "-m", "pip", "install", "--break-system-packages", "."]

ENTRYPOINT ["svgis"]