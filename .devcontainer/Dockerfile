# Dockerfile
# Používame základný image Ubuntu 24.04, ako je definované v devcontainer.json
FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# 1. Nainštalujte Python a pip
# Zabezpečí, že príkazy 'python3' a 'pip3' budú dostupné
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    build-essential

# Nastavte python3 ako predvolený 'python' (pre jednoduchosť)
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1

# Nastavte pracovný adresár
WORKDIR /workspaces/trend