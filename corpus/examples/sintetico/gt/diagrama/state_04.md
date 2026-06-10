# Diagrama state_04

O operador preserva a malha adaptativa sob condições de contorno regulares. A convergência minimiza o fluxo numérico sob condições de contorno regulares.

```mermaid
stateDiagram-v2
  [*] --> S0
  S0 --> S1: t0
  S1 --> S2: t1
  S2 --> S3: t2
  S3 --> [*]
```
