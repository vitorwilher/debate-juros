# O debate dos juros

**Painel aberto e atualizado do debate sobre juros, inflação e dívida pública no Brasil.**
→ **https://vitorwilher.github.io/debate-juros/**

Em setembro de 2026, André Lara Resende propôs derrubar a Selic de forma anunciada, com o argumento
de que os juros altos são o "único motor" da dívida pública. O debate não é novo: em 2017, um artigo
do mesmo autor abriu dois meses de discussão no *Valor Econômico*. Este repositório organiza as duas
rodadas e confronta os argumentos com os dados do Banco Central.

| Página | O que tem |
|:---|:---|
| [Painel](https://vitorwilher.github.io/debate-juros/) | Selic, juro real, dívida bruta, o primário que estabiliza a dívida e a decomposição da dívida bruta desde 2016 |
| [Simulador](https://vitorwilher.github.io/debate-juros/simulador.html) | A trajetória da dívida com e sem a proposta, com controles para custo, crescimento, primário e prêmio de risco |
| [Linha do tempo](https://vitorwilher.github.io/debate-juros/linha-do-tempo.html) | Quem escreveu o quê, de 2017 a 2026 |
| [Quem diz o quê](https://vitorwilher.github.io/debate-juros/posicoes.html) | O mapa das posições em cinco perguntas e os pontos em disputa |
| [Dados e método](https://vitorwilher.github.io/debate-juros/metodo.html) | Fontes, fórmulas e como contribuir |

## Um debate vivo

- **Os dados se atualizam sozinhos.** Uma GitHub Action baixa as séries do SGS/BCB nos dias 5 e 20 de
  cada mês, refaz os gráficos e republica o site.
- **As posições ficam em [`debate.yml`](debate.yml).** Uma intervenção nova é um bloco a mais nesse
  arquivo; a linha do tempo e o mapa de posições se refazem a partir dele.
- **Contribua:** [sugira uma intervenção](../../issues/new?template=sugerir-intervencao.yml) ou abra um
  pull request.

## Estrutura

```
debate.yml               intervenções e posições
dados/sgs/               séries do SGS (atualizadas pela Action)
dados/bcb/               Notas de Estatísticas Fiscais (atualizadas à mão)
scripts/atualizar_sgs.py baixa as séries do SGS
scripts/construir.py     monta site-data/ antes de cada render
*.qmd                    páginas (Quarto + Observable JS)
```

Para rodar localmente: `pip install pandas pyyaml`, `python scripts/atualizar_sgs.py` e `quarto preview`.

## Licença

Código sob MIT; textos, gráficos e `debate.yml` sob CC BY 4.0. Cite como "Análise Macro, O debate dos juros".

Dados: Banco Central do Brasil. Elaboração: [Análise Macro](https://analisemacro.com.br).
