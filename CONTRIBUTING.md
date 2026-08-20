# Contributing to VGTREE

Contributions are welcome through GitHub issues and pull requests.

## Development setup

```bash
git clone https://github.com/scandium1102/vgtree.git
cd vgtree
python -m pip install -e .
python -m unittest discover -s tests -v
```

Use a focused branch. Add a failing regression test before production behavior, make the smallest passing change, and keep public files free of credentials, private paths, personal data, and deployment-specific governance.

Validate every changed Skill with the repository tests and the Agent Skills validator. Validate the plugin manifest before requesting review. Include the exact commands and fresh results in the pull request.

By contributing, you agree that your contribution is licensed under the MIT License.
