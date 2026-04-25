# envault

> A CLI tool for encrypting and syncing `.env` files across team members using GPG keys.

---

## Installation

```bash
pip install envault
```

Or with pipx (recommended):

```bash
pipx install envault
```

---

## Usage

**Initialize envault in your project:**

```bash
envault init
```

**Add a team member's GPG key:**

```bash
envault add-key teammate@example.com
```

**Encrypt and sync your `.env` file:**

```bash
envault lock .env
```

**Decrypt a received `.env` file:**

```bash
envault unlock .env.vault
```

**List all authorized keys:**

```bash
envault keys list
```

> `.env` files are never committed. Only the encrypted `.env.vault` file is shared via your repository or a configured sync backend.

---

## Requirements

- Python 3.8+
- GPG installed on your system (`gpg --version`)

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Contributions welcome. Open an issue or submit a pull request.*