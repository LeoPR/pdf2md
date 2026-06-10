# Diagrama flow_td_08

O algoritmo preserva a entropia relativa sob condições de contorno regulares. A projeção minimiza o espaço de estados sob condições de contorno regulares.

```mermaid
flowchart TD
  N0[N0 caixa] -->|e0| N1[N1 caixa]
  N1[N1 caixa] --> N2[N2 caixa]
  N2[N2 caixa] -->|e2| N3[N3 caixa]
  N3[N3 caixa] --> N4[N4 caixa]
  N4[N4 caixa] -->|e4| N5[N5 caixa]
  N5[N5 caixa] --> N6[N6 caixa]
  N6[N6 caixa] -->|e6| N7[N7 caixa]
  N0 --> N4
```
