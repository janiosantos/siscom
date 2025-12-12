FROM node:20-slim

# Dependências do sistema
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends \
    git curl wget zsh vim nano sudo ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ARG USERNAME=node

# Sudo sem senha para o usuário node (já existe na imagem)
RUN echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
  && chmod 0440 /etc/sudoers.d/${USERNAME}

# Corepack (pnpm/yarn) sem "npm install -g"
RUN corepack enable \
  && corepack prepare pnpm@latest --activate \
  && corepack prepare yarn@stable --activate

# Workspace
WORKDIR /workspace

# Oh My Zsh
USER ${USERNAME}
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended \
  && echo 'export PS1="%F{cyan}⚡ frontend%f %F{blue}%~%f $ "' >> ~/.zshrc

CMD ["sleep", "infinity"]
