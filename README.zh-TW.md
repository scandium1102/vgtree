# VGTREE 繁體中文快速開始

VGTREE 是一套 local-first 的 Tree workflow 引擎、CLI 與 skills-only OpenAI Plugin，讓複雜工作可以被拆成有依賴、有證據、可恢復的分支，並且只在整合與完成閘門真正通過時宣告完成。

核心不會送出遙測，也不需要託管服務。

## 安裝

需要 Python 3.10 以上：

```bash
pip install git+https://github.com/scandium1102/vgtree.git@v1.0.0
vgtree --help
```

## 基本流程

```bash
vgtree classify --task examples/task.json
vgtree init --task examples/task.json --state .vgtree/tasks/example.json
vgtree next --state .vgtree/tasks/example.json
vgtree validate --state .vgtree/tasks/example.json
```

分支執行時，不要直接修改 state JSON：

```bash
vgtree guard --state .vgtree/tasks/example.json --branch build --activity "run bounded implementation batch"
vgtree set-branch --state .vgtree/tasks/example.json --branch build --status IN_PROGRESS
vgtree record-evidence --state .vgtree/tasks/example.json --branch build --evidence examples/evidence.json
vgtree set-branch --state .vgtree/tasks/example.json --branch build --status VERIFIED
```

狀態與 exit code 為：`PASS=0`、`FAIL=1`、`REVIEW_REQUIRED=2`、`BLOCKED=3`。

## Obsidian 配套

既有 Vault 只能做唯讀 audit／plan：

```bash
vgtree obsidian audit --vault /path/to/vault --mode core
vgtree obsidian plan --vault /path/to/vault --mode governed --output /outside/vault/plan.json
```

只有全新或空白目錄可以 scaffold：

```bash
vgtree obsidian scaffold --destination /path/to/new-vault --mode core
```

VGTREE v1 不會對既有 Vault 執行 apply、搬移、改名、覆寫或刪除。

## Plugin 與 six Skills

Plugin 包含六個可組合 Skills：使用與路由、Tree 規劃、Tree 執行、Tree 驗證、知識架構治理，以及 Obsidian workspace 建置。完整安裝方式請看 [Plugin 文件](docs/plugin.md)。

## 兩種 UID 模式

- Core：project UID、owner、registry，以及 Home／Map／Status／Todo。
- Governed：在 Core 上加入每個 managed file 的 file UID、raw-byte SHA-256、provenance、transaction、readback 與 rollback evidence。

詳細內容請看 [UID modes](docs/uid-modes.md) 與 [Obsidian guide](docs/obsidian.md)。
