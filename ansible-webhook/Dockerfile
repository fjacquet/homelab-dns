FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client sshpass git curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir ansible-core
RUN ansible-galaxy collection install \
    community.docker \
    community.general \
    ansible.posix

COPY ansible.cfg /etc/ansible/ansible.cfg
COPY main.py .

# Pre-populate known_hosts for all managed hosts
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
RUN ssh-keyscan -H 172.16.86.11 172.16.86.12 172.16.86.13 172.16.86.14 172.16.86.15 \
    > /root/.ssh/known_hosts 2>/dev/null && chmod 644 /root/.ssh/known_hosts

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
