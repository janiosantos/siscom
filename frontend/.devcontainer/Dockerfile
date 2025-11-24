FROM node:18-slim

# Instalar dependências do sistema
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
        git \
        curl \
        wget \
        zsh \
        vim \
        nano \
        sudo \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
ARG USERNAME=node
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# O usuário 'node' já existe na imagem node oficial, apenas configurar sudo
RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Instalar Oh My Zsh
USER $USERNAME
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Instalar ferramentas globais do Node.js
USER root
RUN npm install -g \
    npm@latest \
    pnpm \
    yarn \
    vercel \
    next \
    eslint \
    prettier \
    typescript

# Configurar diretório de trabalho
WORKDIR /workspace

# Mudar para usuário node
USER $USERNAME

# Configurar prompt do zsh
RUN echo 'export PS1="%F{cyan}⚡ frontend%f %F{blue}%~%f $ "' >> ~/.zshrc

CMD ["sleep", "infinity"]
