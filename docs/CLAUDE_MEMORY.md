# Memória herdada — convenções da máquina

Snapshot das memórias relevantes do Claude no momento da separação
(2026-05-08). Não é "live state" — verificar contra o estado atual
antes de assumir como fato.

Sistema vivo de memória do Claude para este projeto fica em
`~/.claude/projects/c--Users-leona-OneDrive-Documents-Projects-Acad-micos-transmutos-pdf2md/memory/`
quando você abrir uma nova sessão aqui.

---

## Caches centralizados em `Z:\` (reference)

> **Origem:** memória da máquina, estabelecida Maio/2026 (piloto: Goitacaz).
> Documentação canônica em `Z:\caches\README.md`.

**Convenção da máquina:**

- Venvs reais ficam em `Z:\venvs\<nome>`, projetos têm apenas junction
  `.venv` local. **Nunca** apagar `.venv` com `Remove-Item -Recurse`
  (segue link e destrói o venv real). Usar `(Get-Item .venv).Delete()`
  ou `cmd /c rmdir .venv`.

- Env vars já setadas no User scope: `PYTHONPYCACHEPREFIX`,
  `PIP_CACHE_DIR`, `UV_CACHE_DIR`, `RUFF_CACHE_DIR`, `MYPY_CACHE_DIR`,
  `COVERAGE_FILE`, `IPYTHONDIR`, `JUPYTER_CONFIG_DIR`/`DATA_DIR`/`RUNTIME_DIR`,
  `PRE_COMMIT_HOME`, `BLACK_CACHE_DIR`. Não criar overrides por projeto
  sem motivo registrado.

- pytest é exceção (sem env var oficial) — `pyproject.toml` deste
  projeto explicita `cache_dir = "Z:\\caches\\pytest"` em
  `[tool.pytest.ini_options]`.

- **Projeto novo:** só 2 comandos — `py -m venv Z:\venvs\<nome> --prompt <nome>`
  + junction. Tudo o mais é herdado.

- **Projeto legado:** rodar grep por `cache_dir`/`cache-dir` em
  pyproject/pytest.ini/tox.ini/mypy.ini/ruff.toml/.pre-commit-config.yaml
  antes de migrar. Princípio: projeto vence; exceção é melhor que falsa
  uniformidade.

Indicador `(<nome>)` verde no prompt depende de wrapper no `$PROFILE`
lendo `$env:VIRTUAL_ENV_PROMPT` (porque `Activate.ps1` não roda —
ativação é via experiment `pythonTerminalEnvVarActivation`).

---

## Setup deste projeto na primeira abertura

```powershell
cd C:\Users\leona\OneDrive\Documents\Projects\Acadêmicos\transmutos\pdf2md
py -m venv Z:\venvs\pdf2md --prompt pdf2md
cmd /c mklink /J .venv Z:\venvs\pdf2md
.venv\Scripts\python.exe -m pip install -e .[dev]
```

Para o pipeline com GPU (marker-pdf precisa de torch CUDA):

```powershell
.venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cu128
```

Pandoc e Chrome também precisam estar disponíveis no PATH para o
pipeline MD → PDF.

---

## Pendências relevantes do pdf_md_converter (na separação)

- **Round-trip do livro N&C inteiro**: medido só em cap. 4 (95.1%).
  Ideal seria rodar em todos os capítulos para ter distribuição.
- **stats.py após image optimization**: precisou de hack — re-injetar
  `source` e `roundtrip` da run anterior porque eu re-rodei `stats.py`
  sem flags. Idealmente `stats.py` teria `--carry-from <_stats.json>`
  para preservar dados que não dependem das imagens.
- **Multi-iteration só em paper de teste**: rodar em N&C cap. 4
  também para confirmar a estabilidade lá.
- **gen_pdfs.py** importa de outro módulo — checar se está
  auto-suficiente antes de empacotar (T108).

---

*Esta memória foi importada do AulaQuantum em 2026-05-08. A partir
daqui, o Claude vai construir memórias específicas deste projeto.*
