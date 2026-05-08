---
id: T105
titulo: Substituir extração antiga (eliminar _v2 anti-padrão)
status: in_progress
criado_em: 2026-05-07
fase: 1
depende_de: [T001, T102]
blocks: []
tags: [conversor, git, padronizacao]
---

## Contexto
Pasta `_v2` foi criada como sufixo. Anti-padrão: git existe pra isso. Decisão: substituir a antiga pela nova, com commit antes para preservar histórico.

## Objetivo
1. Commit do estado atual (extração antiga preservada no histórico git)
2. Deletar `Quantum_Computation_and_Quantum_Information/` antiga
3. Renomear `_v2` → nome canônico
4. Commit "feat: re-extração via marker GPU (substitui PyMuPDF)"

## Critérios de aceitação
- [ ] T110: commit estado atual
- [ ] T111: rmdir antiga + rename v2 → canônico
- [ ] T112: commit substituição
- [ ] Nenhuma pasta com sufixo _vN no projeto
