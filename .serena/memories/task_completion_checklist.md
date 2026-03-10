# Task Completion Checklist

After completing any code changes:

1. **Ansible lint**: `uvx --with ansible-lint ansible-lint`
2. **YAML lint**: `uvx yamllint .`
3. **Dry-run** (if playbook changed): `ansible-playbook -i inventory.yml <playbook> --check --diff`
4. **Verify FQCN**: all modules use fully qualified collection names
5. **Verify secrets**: `no_log: true` on tasks with vault vars
6. **Verify idempotency**: tasks should be safe to run multiple times
