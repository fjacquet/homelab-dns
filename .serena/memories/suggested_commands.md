# Suggested Commands

## Ansible

```bash
ansible-playbook -i inventory.yml site.yml                    # Full deploy
ansible-playbook -i inventory.yml site.yml --check --diff     # Dry-run
ansible-playbook -i inventory.yml site.yml --tags <tag>       # By phase
ansible-playbook -i inventory.yml update.yml                  # OS patches
ansible-playbook -i inventory.yml update-containers.yml       # Container updates
ansible-vault edit group_vars/all/vault.yml                   # Edit secrets
```

## Linting & Quality

```bash
uvx --with ansible-lint ansible-lint                          # Ansible lint
uvx yamllint .                                                # YAML lint
```

## Python (webhook engine)

```bash
cd ansible-webhook && uvicorn main:app --reload               # Local dev server
```

## Documentation

```bash
uv run tools/serve-docs.py                                    # Local MkDocs preview
```

## System Utils (macOS/Darwin)

```bash
git status / git diff / git log
ls -la / find . -name "*.yml"
grep -r "pattern" .
```
