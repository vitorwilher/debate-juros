"""Baixa as séries do SGS/BCB usadas no painel e grava em dados/sgs/<código>.csv.

Roda todo mês pela GitHub Action (.github/workflows/publicar.yml) e pode ser rodado à mão:
    python scripts/atualizar_sgs.py
Se o BCB estiver fora do ar, mantém o arquivo anterior e segue.
"""
import csv
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

SERIES = {
    4189: "Selic acumulada no mês, anualizada (% a.a.)",
    433: "IPCA, variação mensal (%)",
    13522: "IPCA, acumulado em 12 meses (%)",
    13762: "Dívida bruta do governo geral (% do PIB)",
    5793: "NFSP primárias, setor público consolidado, 12 meses (% do PIB; + = déficit)",
    4382: "PIB acumulado em 12 meses, valores correntes (R$ milhões)",
}
URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{cod}/dados?formato=json&dataInicial=01/01/2000"
DESTINO = Path(__file__).resolve().parent.parent / "dados" / "sgs"


def baixar(cod: int) -> list[dict]:
    req = urllib.request.Request(URL.format(cod=cod), headers={"User-Agent": "painel-debate-juros"})
    for tentativa in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as erro:  # noqa: BLE001
            print(f"  SGS {cod}: tentativa {tentativa + 1} falhou ({erro})")
            time.sleep(5 * (tentativa + 1))
    raise RuntimeError(f"SGS {cod} indisponível")


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    falhas = 0
    for cod, nome in SERIES.items():
        try:
            obs = baixar(cod)
        except RuntimeError as erro:
            print(f"AVISO: {erro}; mantido o arquivo anterior")
            falhas += 1
            continue
        with open(DESTINO / f"{cod}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["data", "valor"])
            for o in obs:
                w.writerow([datetime.strptime(o["data"], "%d/%m/%Y").date().isoformat(), o["valor"]])
        print(f"SGS {cod} ({nome}): {len(obs)} obs., último dado {obs[-1]['data']}")
    return 1 if falhas == len(SERIES) else 0


if __name__ == "__main__":
    sys.exit(main())
