FROM mcr.microsoft.com/powershell:7.5-debian-12

WORKDIR /workspace/web

RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl gnupg python3 python3-pip python3-venv \
  && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
  && apt-get install -y --no-install-recommends nodejs \
  && ln -sf /usr/bin/pwsh /usr/bin/powershell \
  && rm -rf /var/lib/apt/lists/*

COPY web/package*.json ./
RUN npm ci

COPY requirements*.txt /workspace/
COPY tfm_ingestor /workspace/tfm_ingestor
RUN python3 -m pip install --break-system-packages -r /workspace/requirements-dev.txt

COPY web /workspace/web
RUN npm run build

ENV TFM_REPO_ROOT=/workspace
EXPOSE 3000

CMD ["npm", "run", "start"]
