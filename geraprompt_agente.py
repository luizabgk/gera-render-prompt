#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AGENTE GeraPrompt Render (local)
================================
Monta o prompt (lógica do GeraPrompt), escolhe a referência do padrão MN e gera
o render no Magnific via API.

Uso rápido:
  # 1) só monta o prompt e diz a referência (não gasta crédito)
  python geraprompt_agente.py prompt --modo planta --base "C:/.../planta.jpg" --enq top

  # 2) gera no Magnific (precisa de API key válida)
  set MAGNIFIC_API_KEY=sua_chave
  python geraprompt_agente.py gerar --modo 3d --cena lake --aspect 16:9

Configuração da chave: variável de ambiente MAGNIFIC_API_KEY
(ou edite API_KEY abaixo).
"""

import argparse
import base64
from io import BytesIO
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request

# ---------- configuração ----------
API_BASE = "https://api.magnific.com"
API_KEY = os.environ.get("MAGNIFIC_API_KEY", "").strip()

# Pasta das imagens de referência (fonte real: pasta de treinamento)
KIT_DIR = r"\\192.168.0.201\dados\Internet\Luiza\GERENCIAMENTO IA\TREINAMENTO-3D\_REFERENCIA_MN_3D"

REFERENCIAS = {
    "lake":    "mn_web_1.jpg",
    "lago":    "mn_web_1.jpg",
    "praça":   "2009_F_2.jpg",
    "praca":   "2009_F_2.jpg",
    "caminho": "mn_web_6.jpg",
    "street":  "RUA_avenida__EntreVerdes-17.jpg",
    "rua":     "RUA_avenida__EntreVerdes-17.jpg",
    "jardim":  "JARDIM_residencial__residencia-jb.jpg",
    "entrada": "102_NAUTICO_Entrada_24112013_Foto_Henrique_Santos (1).jpg",
    "entrance":"102_NAUTICO_Entrada_24112013_Foto_Henrique_Santos (1).jpg",
}

# ---------- textos (do GeraPrompt) ----------
GEOMETRIA = ("Preservar morfologia urbana, proporções, divisas, largura das vias e a posição "
             "de edificações, equipamentos e áreas de lazer. Manter o mesmo recorte da base, "
             "sem re-enquadrar, esticar ou deformar a geometria.")

PAISAGISMO_MN = (
    "Plantio em blocos e faixas, nunca misturado. Palmeiras altas de tronco fino (royal, coco) "
    "e bismarckia prateada como acento vertical, em grupos de 3 a 5. Árvores de copa ampla "
    "formando massa verde. Gramado aparado em tapete, sem falhas. Florada em faixa curta: ixora "
    "vermelho-tijolo, amarelo-ouro e rosa; bougainville roxo pontuando as vias. Renques de arbusto "
    "aparado como estrutura. Proporção aproximada: 30% árvores de copa, 25% palmeiras, 15% gramíneas, "
    "12% florada, 10% arbustos, 8% gramado. Aplicar apenas onde a base já indica vegetação."
)

MN_EN = ("with high-end tropical landscaping in the Marcelo Novaes style: tall royal palms, bismarckia "
         "and washingtonia palms, broad-canopy trees, manicured lawn, masses of red ixora and golden "
         "yellow flowers, purple bougainvillea, layered planting with flower beds along the streets")

SUFFIX = ("real photograph taken with a full-frame camera, natural daylight, physically based "
          "materials, accurate proportions, ultra-detailed, 8k, sharp, high dynamic range, photorealistic")

NEG_PLANTA = ("Não alterar o traçado, os lotes, as vias, as edificações ou a vegetação indicada. "
              "Não apagar, esmaecer ou deformar as linhas de divisa dos lotes. Não criar vegetação, "
              "construções, quadras ou água onde não existe; não remover o que existe. Sem deformar "
              "a proporção nem esticar a imagem; sem vegetação derretida ou flutuante. Sem aspecto "
              "de CGI, de ilustração ou de maquete, sem texto ou marca d'água.")

NEG_3D = ("cartoon, anime, illustration, painting, plastic-looking CGI, low-poly, distorted "
          "perspective, duplicate windows, floating objects, text, watermark, logo, deformed "
          "people, cluttered composition, noisy, blurry, houses, buildings, houses on lots, "
          "extra buildings, new roads, invented plots, coconut palms, repeated identical trees, "
          "cars on the courts, inconsistent scale")


def build_prompt_planta(base, enq="top", formato="same", paisagismo="mn"):
    base_txt = {"cad": "a base chapada de AutoCAD + Google Earth",
                "r3d": "o render 3D do projeto",
                "drone": "a foto aérea de drone do terreno",
                "ia": "a humanização anterior"}.get(base, "a base")
    enq_txt = {"top": "em vista superior ortogonal, top view, ângulo de 90 graus",
               "ob45": "em vista aérea oblíqua de 45 graus",
               "low": "em vista aérea oblíqua baixa, próxima à linha do horizonte",
               "same": "no mesmo enquadramento e ângulo de câmera da imagem original"}.get(enq, enq)
    fmt_txt = {"same": "mantendo exatamente a proporção da base",
               "16:9": "em formato 16:9 horizontal",
               "4:3": "em formato 4:3",
               "9:16": "em formato 9:16 vertical",
               "3:4": "em formato 3:4 vertical"}.get(formato, formato)

    partes = []
    partes.append(f"Converter {base_txt} em fotografia aérea real do empreendimento concluído, "
                  f"{enq_txt}, {fmt_txt}, com a mesma escala da base, em alta resolução "
                  f"(mínimo 2000 px de largura).")
    partes.append(f"GEOMETRIA\n{GEOMETRIA}")
    partes.append("PAISAGISMO\nA vegetação segue a implantação: fica exatamente onde está na base, "
                  "nem a mais, nem a menos. Preservar posição, espécie, porte e proporção de cada "
                  "árvore, arbusto e área de gramado. Não criar vegetação onde não existe nem omitir "
                  "a existente; arbustos não viram árvores; maciços não viram clareiras.")
    if paisagismo == "mn":
        partes.append(f"PAISAGISMO DO ESCRITÓRIO\n{PAISAGISMO_MN}")
    partes.append("LOTEAMENTO E VIAS\nManter todas as áreas de lote como gramado uniforme e realista, "
                  "com textura de grama aparada. Representar todas as estradas e vias com pavimentação "
                  "de asfalto cinza-claro, mantendo alinhamentos e larguras originais. Preservar as "
                  "linhas de divisão dos lotes com linhas brancas finas e contínuas, nítidas em todo o "
                  "traçado, sem apagar, esmaecer ou deformar.")
    partes.append("ELEMENTOS\nManter a identidade e a quantidade dos equipamentos: quadra de tênis "
                  "tem piso e linhas de demarcação; quadra de areia tem superfície solta; não converter "
                  "uma na outra. Nenhum equipamento vira edificação: quadra permanece quadra, com piso "
                  "e linhas, e não se transforma em casa ou piscina. A água existe apenas onde está "
                  "desenhada e tem tom verde-azulado escuro, com margens naturais e reflexo do céu.")
    partes.append("EDIFICAÇÕES\nManter número, posição, planta e cobertura das edificações; não criar "
                  "construções, quiosques ou equipamentos adicionais. Nenhuma edificação ocupa área de "
                  "vegetação: onde há maciço arbóreo ou área verde, permanece vegetação.")
    partes.append("ACABAMENTOS\nManter as cores, os padrões e as texturas de telhado já indicados na "
                  "imagem original. Manter os revestimentos já indicados na imagem original.")
    partes.append("LUZ E REALISMO\nAplicar iluminação natural suave, com sombras discretas e realistas. "
                  "Fotografia aérea nítida em toda a extensão da imagem: folhagem com volume, sombras "
                  "de contato, asfalto com agregado, telha com textura, leve névoa atmosférica; sem "
                  "aspecto de CGI, maquete ou ilustração.")
    return "\n\n".join(partes), NEG_PLANTA


def build_prompt_3d(cena="lake", paisagismo="mn"):
    cena_txt = {"lake": "view of the lake shore and deck, with reflecting water, palms and flower beds",
                "club": "view of the clubhouse and leisure area, with swimming pool, palms and flower beds",
                "street": "eye-level view of an internal street lined with palms and flower beds",
                "plaza": "view of the central plaza with palms and flower beds",
                "courts": "view of the sports courts surrounded by palms and lawn",
                "entrance": "street-level view of the gated entrance, with palms lining the driveway",
                "aerial45": "oblique aerial view"}.get(cena, cena)
    emp = "high-end gated community with empty residential lots ready to build, tree-lined streets and landscaped common areas"
    parts = [f"{cena_txt} of a {emp}"]
    if paisagismo == "mn":
        parts.append(MN_EN)
    parts.append("empty lots, no houses, no buildings")
    parts.append("in 16:9 horizontal format")
    parts.append("surrounded by dense Atlantic rainforest")
    parts.append("golden hour")
    parts.append("full-frame camera, 35 mm lens at f/8, ISO 100, daylight white balance")
    parts.append("a couple of cars parked in the parking area, away from the courts")
    parts.append(SUFFIX)
    return ", ".join(parts) + ".", NEG_3D


def escolher_referencia(cena):
    chave = (cena or "").lower()
    arquivo = REFERENCIAS.get(chave)
    if not arquivo:
        arquivo = REFERENCIAS["lake"]
    caminho = os.path.join(KIT_DIR, arquivo)
    return arquivo, caminho


GERAPROMPT_HTML = os.environ.get(
    "GERAPROMPT_HTML",
    r"\\192.168.0.201\dados\Internet\Luiza\GERENCIAMENTO IA\geraprompt\urbanismo.html",
)


def gerar_prompt_pelo_geraprompt(modo, config):
    """Abre o HTML REAL do GeraPrompt no Edge headless, configura os campos e lê o prompt."""
    from playwright.sync_api import sync_playwright
    import pathlib

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto(pathlib.Path(GERAPROMPT_HTML).as_uri())
        page.wait_for_timeout(900)
        aba = "hum" if modo == "planta" else "criar"
        page.click(f".tabbtn[data-tab='{aba}']")
        page.wait_for_timeout(300)
        for chave, valor in config.items():
            try:
                page.select_option(f"select[data-k='{chave}']", valor)
            except Exception:
                pass
        page.wait_for_timeout(400)
        prompt = page.eval_on_selector("#prompt", "el => el.value")
        negativo = page.eval_on_selector("#negative", "el => el.value")
        browser.close()
    return prompt, negativo


# ---------- API Magnific ----------
def _post_json(url, payload, timeout=60):
    if not API_KEY:
        raise RuntimeError("ERRO: defina MAGNIFIC_API_KEY (variável de ambiente) antes de gerar.")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"x-magnific-api-key": API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _get_json(url, timeout=60):
    req = urllib.request.Request(url, headers={"x-magnific-api-key": API_KEY})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def upload_imagem(caminho, content_type="image/jpeg"):
    """Faz upload de uma imagem local e devolve o asset_url (para usar como image_url)."""
    resp = _post_json(f"{API_BASE}/v1/ai/uploads/request-url",
                      {"files": [{"content_type": content_type}]})
    f = resp["files"][0]
    upload_url, asset_url = f["upload_url"], f["asset_url"]
    headers = dict(f["headers"])
    with open(caminho, "rb") as fh:
        raw = fh.read()
    req = urllib.request.Request(upload_url, data=raw, headers=headers, method="PUT")
    with urllib.request.urlopen(req, timeout=120) as r:
        r.read()
    return asset_url


def listar_loras():
    """Lista os LoRAs de estilo concluídos na conta Magnific."""
    if not API_KEY:
        raise RuntimeError("defina MAGNIFIC_API_KEY para listar os LoRAs")
    raw = _get_json(f"{API_BASE}/v1/ai/loras", timeout=30)
    d = raw.get("data", raw)
    itens = []
    for item in (d.get("customs") or []):
        tr = item.get("training") or {}
        if str(tr.get("status", "")).lower() != "completed":
            continue
        itens.append({
            "id": str(item.get("id", "")),
            "name": str(item.get("name") or item.get("id")),
            "type": str(item.get("type") or "style"),
        })
    itens.sort(key=lambda x: x["name"].lower())
    return itens


def gerar_prompt_por_imagem(imagem, timeout_s=180):
    """Analisa uma imagem e devolve um prompt descritivo (API Image to Prompt).

    Aceita caminho local ou URL. Local é enviado pelo endpoint de upload.
    """
    image_ref = imagem
    if os.path.exists(imagem):
        image_ref = upload_imagem(imagem)
    resp = _post_json(f"{API_BASE}/v1/ai/image-to-prompt", {"image": image_ref}, timeout=60)
    d = resp.get("data", resp)
    task_id = d.get("task_id") or d.get("id")
    if not task_id:
        raise RuntimeError("a API não devolveu task_id para Image to Prompt")
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        raw = _get_json(f"{API_BASE}/v1/ai/image-to-prompt/{task_id}")
        d = raw.get("data", raw)
        status = str(d.get("status", "")).upper()
        if status in ("COMPLETED", "SUCCESS", "DONE"):
            for item in (d.get("generated") or []):
                if not isinstance(item, str):
                    continue
                if item.startswith("http://") or item.startswith("https://"):
                    with urllib.request.urlopen(item, timeout=60) as r:
                        return r.read().decode("utf-8", "replace").strip()
                return item.strip()
            raise RuntimeError("Image to Prompt concluiu sem texto gerado")
        if status in ("FAILED", "ERROR", "CANCELED"):
            raise RuntimeError(f"Image to Prompt falhou: {json.dumps(raw)[:500]}")
        time.sleep(3)
    raise RuntimeError("Tempo esgotado aguardando Image to Prompt")


ASPECT_MAP = {
    "16:9": "widescreen_16_9",
    "4:3": "classic_4_3",
    "3:4": "traditional_3_4",
    "9:16": "social_story_9_16",
    "1:1": "square_1_1",
    "3:2": "standard_3_2",
    "2:3": "portrait_2_3",
    "2:1": "horizontal_2_1",
    "1:2": "vertical_1_2",
    "21:9": "film_horizontal_21_9",
}


def imagem_para_data_uri(caminho, max_bytes=9_500_000, max_side=2048):
    """Converte imagem local em data URI, comprimindo se necessário."""
    from PIL import Image
    mime = mimetypes.guess_type(str(caminho))[0] or "image/jpeg"
    raw = open(caminho, "rb").read()
    if len(raw) <= max_bytes:
        return f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
    im = Image.open(caminho).convert("RGB")
    im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = BytesIO()
    im.save(buf, "JPEG", quality=92, optimize=True)
    raw = buf.getvalue()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def gerar_no_seedream_edit(prompt, aspect="4:3", reference_path=None,
                           resolution="2k", thinking_level="high", seed=12345):
    """Gera/edita com Seedream 5 Pro Edit, preservando melhor a imagem base."""
    if not reference_path or not os.path.exists(reference_path):
        raise RuntimeError("Seedream precisa de uma imagem de referência.")
    if resolution not in ("1.5k", "2k"):
        resolution = "2k"
    payload = {
        "prompt": prompt,
        "reference_images": [imagem_para_data_uri(reference_path)],
        "resolution": resolution,
        "aspect_ratio": ASPECT_MAP.get(aspect, "classic_4_3"),
        "thinking_level": thinking_level,
    }
    if seed is not None:
        payload["seed"] = int(seed)
    data = _post_json(f"{API_BASE}/v1/ai/text-to-image/seedream-v5-pro-edit", payload, timeout=180)
    d = data.get("data", data)
    return d.get("task_id") or d.get("id")


def gerar_no_magnific(prompt, aspect="16:9", estilo="realism",
                      structure_path=None, structure_strength=90,
                      lora_name=None, style_reference_path=None,
                      adherence=35, hdr=30, engine="magnific_sharpy",
                      creative_detailing=25, resolution="2k"):
    """Cria a tarefa no Mystic usando o schema oficial da API.

    - structure_reference: imagem base64 que preserva o traçado/geometria.
    - styling.styles: LoRA de estilo pelo NOME (não pelo ID).
    - LoRA é ignorado pela API quando há structure_reference ou style_reference.
    """
    payload = {
        "prompt": prompt,
        "aspect_ratio": ASPECT_MAP.get(aspect, "widescreen_16_9"),
        "resolution": resolution,
        "engine": engine,
        "creative_detailing": int(creative_detailing),
    }
    if structure_path and os.path.exists(structure_path):
        payload["structure_reference"] = imagem_para_data_uri(structure_path)
        payload["structure_strength"] = int(structure_strength)
    if style_reference_path and os.path.exists(style_reference_path):
        payload["style_reference"] = imagem_para_data_uri(style_reference_path)
        payload["adherence"] = int(adherence)
        payload["hdr"] = int(hdr)
    if lora_name and not structure_path and not style_reference_path:
        # Com LoRA, deixe o modelo padrão: super_real/fluid/etc. ignoram LoRA.
        payload["styling"] = {"styles": [{"name": str(lora_name), "strength": 100}]}
    else:
        payload["model"] = estilo
    data = _post_json(f"{API_BASE}/v1/ai/mystic", payload, timeout=120)
    d = data.get("data", data)
    return d.get("task_id") or d.get("id")


def aguardar(task_id, modelo="mystic", timeout_s=600):
    """Faz polling da tarefa até completar e devolve a URL do resultado."""
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        raw = _get_json(f"{API_BASE}/v1/ai/{modelo}/{task_id}")
        d = raw.get("data", raw)
        status = str(d.get("status", "")).upper()
        if status in ("COMPLETED", "SUCCESS", "DONE"):
            gen = d.get("generated") or []
            urls = []
            for item in gen:
                if isinstance(item, str):
                    urls.append(item)
                elif isinstance(item, dict):
                    for k in ("url", "image_url", "src"):
                        if item.get(k):
                            urls.append(item[k])
                            break
            return urls[0] if urls else None
        if status in ("FAILED", "ERROR", "CANCELED"):
            raise RuntimeError(f"Tarefa falhou: {json.dumps(raw)[:500]}")
        time.sleep(5)
    raise RuntimeError("Tempo esgotado aguardando a geração.")


def baixar(url, destino):
    with urllib.request.urlopen(url, timeout=120) as r:
        with open(destino, "wb") as f:
            f.write(r.read())
    return destino


# ---------- CLI ----------
def main():
    ap = argparse.ArgumentParser(description="Agente GeraPrompt Render")
    ap.add_argument("acao", choices=["prompt", "prompt-imagem", "gerar"])
    ap.add_argument("--modo", choices=["planta", "3d"], default="planta")
    ap.add_argument("--base", default="cad", help="cad | r3d | drone | ia")
    ap.add_argument("--enq", default="top", choices=["top", "ob45", "low", "same"])
    ap.add_argument("--formato", default="same", choices=["same", "16:9", "4:3", "9:16", "3:4"])
    ap.add_argument("--cena", default="lake", help="lake | club | street | plaza | courts | entrance | aerial45")
    ap.add_argument("--aspect", default="16:9")
    ap.add_argument("--paisagismo", default="mn", choices=["mn", "livre"])
    ap.add_argument("--out", default="render_magnific.png")
    ap.add_argument("--base-img", default="", help="caminho da planta (modo planta) para usar como base")
    ap.add_argument("--ref-img", default="", help="caminho de uma imagem de referência específica (pasta 3D)")
    ap.add_argument("--lora-name", default="", help="nome de um LoRA de estilo (use GET /v1/ai/loras)")
    ap.add_argument("--estilo", default="realism", choices=["realism", "super_real", "flexible", "fluid", "zen"])
    ap.add_argument("--engine", default="magnific_sharpy", choices=["automatic", "magnific_sharpy", "magnific_sparkle", "magnific_illusio"])
    ap.add_argument("--resolucao", default="2k", choices=["1k", "2k", "4k"])
    ap.add_argument("--imagem-prompt", default="", help="imagem para gerar prompt automático (Image to Prompt)")
    args = ap.parse_args()

    if args.acao == "prompt-imagem":
        if not args.imagem_prompt or not os.path.exists(args.imagem_prompt):
            raise SystemExit("ERRO: informe --imagem-prompt com um arquivo existente.")
        if not API_KEY:
            raise SystemExit("ERRO: defina MAGNIFIC_API_KEY antes de gerar o prompt.")
        prompt = gerar_prompt_por_imagem(args.imagem_prompt)
        print(prompt)
        saida = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_prompt.txt")
        with open(saida, "w", encoding="utf-8") as f:
            f.write(prompt + "\n")
        print(f"(prompt salvo em {saida})")
        return

    if args.modo == "planta":
        config = {"h.base": args.base, "h.enq": args.enq, "h.formato": args.formato,
                  "h.pais": "full", "h.padrao": args.paisagismo}
        ref_nome, ref_path = escolher_referencia("lake")
    else:
        config = {"c.cena": args.cena, "c.pais3": args.paisagismo, "c.formato3": args.formato}
        ref_nome, ref_path = escolher_referencia(args.cena)

    if args.ref_img and os.path.exists(args.ref_img):
        ref_path = args.ref_img
        ref_nome = os.path.basename(ref_path)

    # Usa o HTML REAL do GeraPrompt (com fallback para a cópia interna)
    try:
        prompt, neg = gerar_prompt_pelo_geraprompt(args.modo, config)
        print("[prompt gerado pelo GeraPrompt HTML]")
    except Exception as e:
        print(f"[fallback] Playwright falhou ({e}); usando cópia interna.")
        if args.modo == "planta":
            prompt, neg = build_prompt_planta(args.base, args.enq, args.formato, args.paisagismo)
        else:
            prompt, neg = build_prompt_3d(args.cena, args.paisagismo)

    print("=" * 70)
    print("PROMPT POSITIVO")
    print("=" * 70)
    print(prompt)
    print("\n" + "=" * 70)
    print("PROMPT NEGATIVO")
    print("=" * 70)
    print(neg)
    print("\n" + "=" * 70)
    print(f"LORA: {args.lora_name or '(nenhum)'}")
    print(f"REFERÊNCIA DE ESTILO: {ref_nome}")
    print(f"(caminho: {ref_path})")
    print("=" * 70)

    # salva o prompt em UTF-8 (para copiar sem o problema de console)
    saida_prompt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_prompt.txt")
    with open(saida_prompt, "w", encoding="utf-8") as f:
        f.write(prompt + "\n\n--- NEGATIVE / NEGATIVO ---\n" + neg + "\n\nREFERENCIA: " + ref_nome)
    print(f"(prompt salvo em {saida_prompt})")

    if args.acao == "prompt":
        print("\n[modo prompt] Nada foi gerado. Para gerar, rode com 'gerar' e a chave válida.")
        return

    if not API_KEY:
        print("\nERRO: defina MAGNIFIC_API_KEY antes de gerar.")
        sys.exit(1)

    print("\nGerando no Magnific...")
    try:
        structure_path = None
        if args.modo == "planta" and args.base_img and os.path.exists(args.base_img):
            structure_path = args.base_img
            print(f"Usando como estrutura: {args.base_img}")
        elif os.path.exists(ref_path):
            structure_path = ref_path
            print(f"Usando como estrutura: {ref_nome}")
        task_id = gerar_no_magnific(prompt, args.aspect, args.estilo,
                                    structure_path=structure_path,
                                    lora_name=args.lora_name or None,
                                    engine=args.engine,
                                    resolution=args.resolucao)
        print(f"task_id: {task_id}")
        url = aguardar(task_id)
        if not url:
            print("Não encontrei URL de resultado na resposta.")
            sys.exit(1)
        baixar(url, args.out)
        print(f"Render salvo em: {args.out}")
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:500]}")
        sys.exit(1)


if __name__ == "__main__":
    main()

