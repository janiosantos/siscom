FROM python:3.12-bullseye

# Instalar dependências do sistema
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        git \
        curl \
        wget \
        zsh \
        build-essential \
        libpq-dev \
        postgresql-client \
        redis-tools \
        vim \
        nano \
        sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Instalar Oh My Zsh
USER $USERNAME
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Configurar ambiente Python
USER root
RUN pip install --upgrade pip setuptools wheel

# Instalar ferramentas de desenvolvimento
RUN pip install \
    black \
    flake8 \
    isort \
    mypy \
    pytest \
    pytest-cov \
    pytest-asyncio \
    ipython \
    ipdb \
    pre-commit

# Configurar diretório de trabalho
WORKDIR /workspace

# Mudar para usuário vscode
USER $USERNAME

# Configurar prompt do zsh
RUN echo 'export PS1="%F{green}🐍 backend%f %F{blue}%~%f $ "' >> ~/.zshrc

CMD ["sleep", "infinity"]
