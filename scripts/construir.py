"""Monta os dados do site a partir de dados/ e de debate.yml (roda antes de cada render).

Saídas em site-data/:
  numeros.json        cartões do painel e valores iniciais do simulador
  decomposicao.csv    contribuições anuais à variação da dívida bruta (formato FMI)
  historico.csv       DBGG, Selic e IPCA mensais
  debate.json         intervenções e perguntas do debate
"""
import csv
import json
from pathlib import Path

import pandas as pd
import yaml

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "site-data"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def sgs(cod: int) -> pd.Series:
    d = pd.read_csv(RAIZ / "dados" / "sgs" / f"{cod}.csv", parse_dates=["data"])
    return d.set_index("data")["valor"].astype(float)


def mes_ano(ts) -> str:
    return f"{MESES[ts.month - 1]}/{ts.year}"


def decomposicao(ipca_m: pd.Series) -> pd.DataFrame:
    """Fatores condicionantes da DBGG (BCB, Tabela 19) com juros e PIB em termos reais."""
    fg = pd.read_csv(RAIZ / "dados" / "bcb" / "fatores_dbgg.csv")
    fg["fim"] = pd.to_datetime(fg["periodo"] + "-01")
    fg["d_ant"] = fg["saldo"] - fg["variacao"]
    fg["theta"] = fg["d_ant"] / (fg["d_ant"] + fg["efeito_pib"]) - 1   # crescimento nominal
    fg["pi"] = [
        (1 + ipca_m[(ipca_m.index >= f"{f.year}-01-01") & (ipca_m.index <= f)] / 100).prod() - 1
        for f in fg["fim"]
    ]
    fg["g"] = (1 + fg["theta"]) / (1 + fg["pi"]) - 1
    fg["erosao"] = fg["d_ant"] * (fg["theta"] - fg["g"]) / (1 + fg["theta"])
    fg["juro_real"] = fg["juros"] - fg["erosao"]
    fg["cresc_real"] = fg["efeito_pib"] + fg["erosao"]
    fg["outros"] = fg["outros_externos"] + fg["reconhecimento"] + fg["privatizacoes"]
    resid = (fg["juro_real"] + fg["cresc_real"] + fg["emissoes"] + fg["ajuste_cambial"]
             + fg["outros"] - fg["variacao"]).abs().max()
    assert resid < 1e-9, f"identidade não fecha: {resid}"
    fg["rotulo"] = [str(f.year) if f.month == 12 else f"{f.year} (jan–{MESES[f.month - 1]})"
                    for f in fg["fim"]]
    fg["parcial"] = fg["fim"].dt.month != 12
    return fg


def main() -> None:
    SAIDA.mkdir(exist_ok=True)
    selic, ipca_m, ipca12 = sgs(4189), sgs(433), sgs(13522)
    dbgg, nfsp_prim, pib12 = sgs(13762), sgs(5793), sgs(4382)
    nef = yaml.safe_load(open(RAIZ / "dados" / "bcb" / "nef.yml"))

    # ---- decomposição da dívida bruta
    fg = decomposicao(ipca_m)
    cols = {"juro_real": "Juro real", "cresc_real": "Crescimento real",
            "emissoes": "Emissões líquidas", "ajuste_cambial": "Câmbio", "outros": "Outros"}
    with open(SAIDA / "decomposicao.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rotulo", "ordem", "parcial", "componente", "valor", "variacao", "erosao",
                    "juros_nominais", "saldo"])
        for i, r in fg.iterrows():
            for c, nome in cols.items():
                w.writerow([r["rotulo"], i, int(r["parcial"]), nome, round(r[c], 3),
                            round(r["variacao"], 3), round(r["erosao"], 3),
                            round(r["juros"], 3), round(r["saldo"], 2)])
    dez = fg[~fg["parcial"]]
    soma = {c: round(float(dez[c].sum()), 1) for c in
            ["variacao", "juros", "erosao", "juro_real", "cresc_real", "emissoes",
             "ajuste_cambial", "outros"]}
    nivel_ini = float(dbgg[dbgg.index == f"{dez['fim'].iloc[0].year - 1}-12-01"].iloc[0])
    nivel_fim = float(dbgg[dbgg.index == dez["fim"].iloc[-1]].iloc[0])

    # ---- a conta de hoje
    ult = min(dbgg.index.max(), pib12.index.max(), nfsp_prim.index.max(), ipca12.index.max())
    theta = pib12[ult] / pib12[ult - pd.DateOffset(years=1)] - 1
    d = dbgg[ult]
    custo = nef["custo_implicito_dbgg_12m"] / 100
    pbstar = (custo - theta) / (1 + theta) * d
    sel_mes = selic.index.max()
    juro_real = ((1 + selic[sel_mes] / 100) / (1 + ipca12[ipca12.index.max()] / 100) - 1) * 100

    numeros = {
        "atualizado_em": pd.Timestamp.today().strftime("%d/%m/%Y"),
        "referencia": mes_ano(ult),
        "selic": {"valor": round(selic[sel_mes], 2), "ref": mes_ano(sel_mes)},
        "ipca12": {"valor": round(ipca12[ipca12.index.max()], 2), "ref": mes_ano(ipca12.index.max())},
        "juro_real_expost": round(juro_real, 2),
        "dbgg": {"valor": round(d, 2), "ref": mes_ano(ult)},
        "primario": {"valor": round(-nfsp_prim[ult], 2), "ref": mes_ano(ult)},
        "pib_nominal_12m": round(100 * theta, 2),
        "custo_dbgg": {"valor": nef["custo_implicito_dbgg_12m"], "ref": nef["referencia"],
                       "fonte": nef["fonte"]},
        "custo_lara_resende": nef["custo_medio_lara_resende"],
        "pbstar": round(pbstar, 2),
        "selic_1pp_dbgg": nef["selic_1pp_dbgg"],
        "decomp": {"inicio": int(dez["fim"].iloc[0].year), "fim": int(dez["fim"].iloc[-1].year),
                   "soma": soma, "nivel_ini": round(nivel_ini, 1), "nivel_fim": round(nivel_fim, 1),
                   "revisoes": round(nivel_fim - nivel_ini - soma["variacao"], 1)},
    }
    ix = pd.read_csv(RAIZ / "dados" / "bcb" / "dbgg_indexador.csv", index_col=0)["valor"]
    vc = pd.read_csv(RAIZ / "dados" / "bcb" / "dbgg_vencimentos.csv", index_col=0).sum()
    numeros["estrutura"] = {"selic": round(ix["selic"], 1), "precos": round(ix["precos"], 1),
                            "prefixado": round(ix["prefixado"], 1), "cambial": round(ix["cambial"], 1),
                            "vence_12m": round(100 * vc["ate1"] / vc["total"], 1)}
    (SAIDA / "numeros.json").write_text(json.dumps(numeros, ensure_ascii=False, indent=2))

    # ---- histórico mensal
    h = pd.concat({"dbgg": dbgg, "selic": selic, "ipca12": ipca12}, axis=1, sort=True)
    h = h[h.index >= "2006-12-01"].round(2)
    h.index.name = "data"
    h.reset_index().assign(data=lambda x: x["data"].dt.strftime("%Y-%m-%d")).to_csv(
        SAIDA / "historico.csv", index=False)

    # ---- debate
    deb = yaml.safe_load(open(RAIZ / "debate.yml"))
    for it in deb["intervencoes"]:
        it["data"] = str(it["data"])
        it.setdefault("posicoes", {})
    deb["intervencoes"].sort(key=lambda x: x["data"])
    (SAIDA / "debate.json").write_text(json.dumps(deb, ensure_ascii=False, indent=2))

    print(f"site-data: referência {numeros['referencia']}, DBGG {d:.1f}% do PIB, pb* {pbstar:.1f}%, "
          f"{len(deb['intervencoes'])} intervenções")


if __name__ == "__main__":
    main()
