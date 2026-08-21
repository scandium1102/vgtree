# VGTREE 繁體中文指南

把複雜工作分成可以驗證成果的樹狀分支。

**先畫出完整成果，再覆蓋所有必要分支；廣度通過後才深入，最後用可檢查的證據收據證明完成。**

VGTREE 是給 ChatGPT、Codex、其他 Agent 與 Obsidian 使用的 local-first 工作流系統。目錄中的 six Skills 安裝後即可使用；選配的 Python Engine 會加入 deterministic schema、狀態轉換、Coverage Gate、Receipts 與 JSON CLI。

VGTREE 採 MIT License，免費、無帳號、無託管服務、無 MCP、無遙測，也不會自動修改既有 Obsidian Vault。

## 兩種模式

- **ENGINE**：偵測到相容的 VGTREE 1.1 CLI 時，由機器計算閘門，才可以依真實輸出回報 `PASS`。
- **SKILL_ONLY**：不安裝軟體，使用 Plugin 內附的 templates、schemas 與 references 進行規劃、紀錄與審查；必須回報 `engine_validation=NOT_RUN`，整體最高為 `REVIEW_REQUIRED`。

Skills 不會自動安裝 Engine。

## 安裝 Engine

需要 Python 3.10 以上：

```bash
pip install vgtree==1.1.0
vgtree --version
```

PyPI 正式發布前，可以用精確 GitHub tag：

```bash
pip install git+https://github.com/scandium1102/vgtree.git@v1.1.0
vgtree --help
```

OpenAI universal Plugins Directory 核准後，可直接安裝 Skills-only plugin。

## Map → Cover → Deepen → Prove

### 1. Capability Map：先長出完整棵樹

Capability Map 必須列出完整成果面、共享介面、高風險 `PRE_EXECUTION` owner、minimum viable state 與 final acceptance：

```bash
vgtree map validate --map examples/capability-map.json
vgtree map compile --map examples/capability-map.json --output task.json
vgtree classify --task task.json
vgtree init --task task.json --state state.json
```

### 2. Coverage Gate：先完成廣度覆蓋

State 2.1 會要求每個 `coverage_required` branch 都有精確 baseline evidence。Baseline 只證明廣度已存在，不等於完成。

```bash
vgtree record-evidence --state state.json --branch authorize --evidence examples/baseline-evidence.json
vgtree coverage --state state.json
```

### 3. Deepen：通過後才加深

`REQUIRED` 在 coverage 不足時會阻擋 deep work；`ADVISORY` 若要提前深入，必須留下原因。

```bash
vgtree advance-depth --state state.json
vgtree guard --state state.json --branch deploy --activity "bounded implementation" --depth deep
```

### 4. Receipts：把證據綁到精確 bytes

詳細 Tool Receipts 留在本機 sidecar 檔案；state 只保存由相同 bytes 產生的 compact evidence。

```bash
vgtree receipt validate --root examples --receipt examples/receipt.json
vgtree receipt evidence --root examples --receipt examples/receipt.json --output receipt-evidence.json
vgtree record-evidence --state state.json --branch deploy --evidence receipt-evidence.json
```

Branch 通過仍不等於整體完成；integration 與 final-verification 是獨立閘門：

```bash
vgtree record-evidence --state state.json --evidence integration.json
vgtree next --state state.json
vgtree record-evidence --state state.json --evidence final-verification.json
vgtree complete --state state.json
```

Exit code：`PASS=0`、`FAIL=1`、`REVIEW_REQUIRED=2`、`BLOCKED=3`。

## six Skills 與 Context Budget

VGTREE 保持六個穩定 Skills：

- `using-vgtree`
- `planning-tree-work`
- `executing-tree-work`
- `verifying-tree-work`
- `governing-knowledge-architecture`
- `building-obsidian-workspaces`

Context Budget 預設只啟用一個 primary Skill，加上最多一個 support Skill。額外 bundle 必須有名稱、原因與 unload condition。

## Obsidian 是核心整合

VGTREE 把 Tree workflow 與 UID-first 知識架構結合：

- **Core**：project UID、canonical owner/root、registry、Home、Map、Status、Todo，以及高風險工作的 rollback。
- **Governed**：在 Core 上加入 file UID、raw-byte SHA-256、provenance、lineage、journaled transaction、reference coverage、readback 與 rollback evidence。

既有 Vault 只能 audit／plan，不修改內容：

```bash
vgtree obsidian audit --vault /path/to/vault --mode core
vgtree obsidian plan --vault /path/to/vault --mode governed --output /outside/vault/plan.json
```

只有全新或空白路徑能 scaffold：

```bash
vgtree obsidian scaffold --destination /path/to/new-vault --mode core
```

VGTREE 1.1 不會對既有 Vault 執行 apply、move、rename、rewrite 或 delete。

## 信任邊界

- Capability Map 通過只代表契約一致，不代表規劃假設一定正確。
- Baseline evidence 不能取代 Definition of Done、integration 或 final-verification。
- Receipt validation 是結構與 exact-byte binding；工具輸出的真實性仍由原工具與 readback 負責。
- SKILL_ONLY 不能把模板審查說成 Engine `PASS`。
- 外部發布、破壞性工作、付款、帳號與身分驗證仍需要使用者／host 的即時授權。
- VGTREE 無 analytics、cookies、remote fonts、帳號或遙測。

## 更多文件

- [Architecture](docs/architecture.md)
- [Plugin 與 Skills](docs/plugin.md)
- [Obsidian](docs/obsidian.md)
- [UID modes](docs/uid-modes.md)
- [Security](SECURITY.md)
- [Privacy](PRIVACY.md)
- [Terms](TERMS.md)
- [Support](SUPPORT.md)
