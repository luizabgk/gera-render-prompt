#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeraPrompt Render — GUI separada (gerador de CENAS 3D via API do Magnific).
Não tem vínculo com o GeraPrompt HTML.
"""
import json
import logging
import os
import queue
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geraprompt_agente as ag

ag.API_KEY = os.environ.get('MAGNIFIC_API_KEY', ag.API_KEY).strip() or ag.API_KEY

LOG_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "GeraPromptRender"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "gerarender.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)

PROMPT_PADRAO = ""
REF_DIR = Path(r"F:\Internet\Luiza\GERENCIAMENTO IA\geraprompt\referencias")
REF_MANIFEST = REF_DIR / "manifest.json"


class App:
    def __init__(self, root):
        self.root = root
        root.title("GeraPrompt Render v2.6 — biblioteca visual")
        root.geometry("900x860")
        self.ref = ""
        self.ref_linhas = ""
        self.pasta = ""
        self.foto = None
        self._gallery_thumbs = []
        self.lora_por_label = {"Nenhum (sem LoRA)": None}
        self.nao_expandir_agua = tk.BooleanVar(value=True)
        self.fila_ui = queue.Queue()
        self.motor_map = {
            "Seedream 5 Pro Edit (fiel à base)": "seedream",
            "Mystic (cena 3D/conceito)": "mystic",
        }
        self.engine_map = {
            "Sharpy (foto/arquitetura)": "magnific_sharpy",
            "Automático": "automatic",
            "Sparkle (realista intermediário)": "magnific_sparkle",
            "Illusio (ilustração/natureza)": "magnific_illusio",
        }
        self.lora_count = 0
        self.gerando = False
        self.job_id = 0
        self.tempo_inicio = None
        self.modo_qualidade = tk.BooleanVar(value=True)
        self.checar_conteudo = tk.BooleanVar(value=True)
        self.escolher_manual = tk.BooleanVar(value=True)
        self.fixar_geracao = tk.BooleanVar(value=False)

        # 1) referência
        f1 = tk.Frame(root)
        f1.pack(fill="x", padx=14, pady=8)
        tk.Button(f1, text="1. Biblioteca de referências (estilo)", width=30, command=lambda: self.abrir_biblioteca("ref")).pack(side="left")
        self.lbl_ref = tk.Label(f1, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_ref.pack(side="left", padx=8)
        tk.Button(f1, text="Limpar", command=self.limpar_ref).pack(side="left", padx=(0, 4))
        tk.Label(root, text="A imagem de referência entra como estilo no Mystic; não é estrutura de planta.",
                 anchor="w", fg="#777").pack(fill="x", padx=14)
        f1b = tk.Frame(root)
        f1b.pack(fill="x", padx=14, pady=(0, 4))
        tk.Button(f1b, text="1b. Biblioteca de linhas de lote", width=30, command=lambda: self.abrir_biblioteca("linhas")).pack(side="left")
        self.lbl_linhas = tk.Label(f1b, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_linhas.pack(side="left", padx=8)
        tk.Button(f1b, text="Limpar", command=self.limpar_linhas).pack(side="left", padx=(0, 4))
        tk.Label(root, text="Use a planta com divisas para as linhas dos lotes continuarem aparecendo. O estilo fica na referência 1.",
                 anchor="w", fg="#777").pack(fill="x", padx=14)
        self.chk_agua = tk.Checkbutton(
            root,
            text="Manter lagos e corpos d'água no tamanho e contorno originais (só se houver referência)",
            variable=self.nao_expandir_agua,
        )
        self.chk_agua.pack(fill="x", padx=14)
        self.chk_agua.config(state="disabled")

        # 2) prompt
        tk.Label(root, text="2. Prompt (cole o do GeraPrompt ou digite):", anchor="w").pack(fill="x", padx=14)
        self.txt_prompt = tk.Text(root, height=8, font=("Consolas", 9))
        self.txt_prompt.pack(fill="both", padx=14, pady=4)
        self.txt_prompt.insert("end", PROMPT_PADRAO)
        tk.Label(root, text="Cole o prompt do GeraPrompt ou digite o prompt da cena.",
                 anchor="w", fg="#666").pack(fill="x", padx=14)

        f_motor = tk.Frame(root)
        f_motor.pack(fill="x", padx=14, pady=4)
        tk.Label(f_motor, text="Motor:").pack(side="left")
        self.cmb_motor = ttk.Combobox(f_motor, values=list(self.motor_map), state="readonly", width=44)
        self.cmb_motor.set("Mystic (cena 3D/conceito)")
        self.cmb_motor.pack(side="left", padx=4)
        self.cmb_motor.bind("<<ComboboxSelected>>", lambda e: self.atualizar_motor())

        # 3) opções
        f2 = tk.Frame(root)
        f2.pack(fill="x", padx=14, pady=4)
        tk.Label(f2, text="Proporção:").pack(side="left")
        self.cmb_aspect = ttk.Combobox(f2, values=["16:9", "1:1", "4:3", "3:4", "9:16", "3:2"], width=8)
        self.cmb_aspect.set("16:9")
        self.cmb_aspect.pack(side="left", padx=4)
        tk.Label(f2, text="Estilo:").pack(side="left", padx=(14, 0))
        self.cmb_estilo = ttk.Combobox(f2, values=["realism", "super_real", "flexible", "fluid", "zen"], width=12)
        self.cmb_estilo.set("realism")
        self.cmb_estilo.pack(side="left", padx=4)

        f_opts2 = tk.Frame(root)
        f_opts2.pack(fill="x", padx=14, pady=4)
        tk.Label(f_opts2, text="Acabamento:").pack(side="left")
        self.cmb_engine = ttk.Combobox(f_opts2, values=list(self.engine_map), state="readonly", width=28)
        self.cmb_engine.set("Sharpy (foto/arquitetura)")
        self.cmb_engine.pack(side="left", padx=4)
        tk.Label(f_opts2, text="Resolução:").pack(side="left", padx=(12, 0))
        self.cmb_resolucao = ttk.Combobox(f_opts2, values=["2k", "4k"], state="readonly", width=5)
        self.cmb_resolucao.set("2k")
        self.cmb_resolucao.pack(side="left", padx=4)
        self.chk_qualidade = tk.Checkbutton(
            root,
            text="Qualidade máxima: gerar 2 versões e escolher a mais nítida (2 gerações)",
            variable=self.modo_qualidade,
        )
        self.chk_qualidade.pack(fill="x", padx=14)
        self.chk_conteudo = tk.Checkbutton(
            root,
            text="Verificar conteúdo: rejeitar água/cena errada (usa 2 análises extras)",
            variable=self.checar_conteudo,
        )
        self.chk_conteudo.pack(fill="x", padx=14)
        self.chk_manual = tk.Checkbutton(
            root,
            text="Escolher manualmente entre as 2 versões (abre comparador)",
            variable=self.escolher_manual,
        )
        self.chk_manual.pack(fill="x", padx=14)
        self.chk_fixar = tk.Checkbutton(
            root,
            text="Fixar geração: mesmos parâmetros geram o mesmo resultado (Mystic)",
            variable=self.fixar_geracao,
        )
        self.chk_fixar.pack(fill="x", padx=14)

        # 3b) LoRA opcional
        f_lora = tk.Frame(root)
        f_lora.pack(fill="x", padx=14, pady=4)
        tk.Label(f_lora, text="LoRA (opcional):").pack(side="left")
        self.cmb_lora = ttk.Combobox(f_lora, values=list(self.lora_por_label), state="readonly", width=42)
        self.cmb_lora.set("Nenhum (sem LoRA)")
        self.cmb_lora.pack(side="left", padx=4)
        self.btn_lora = tk.Button(f_lora, text="Atualizar", command=self.carregar_loras)
        self.btn_lora.pack(side="left", padx=4)
        self.lora_hint = tk.Label(root, text="LoRA é um estilo treinado; não é a imagem de referência. A referência é o botão 1 acima.",
                                  anchor="w", fg="#777")
        self.lora_hint.pack(fill="x", padx=14)
        f_lora_str = tk.Frame(root)
        f_lora_str.pack(fill="x", padx=14, pady=(0, 4))
        tk.Label(f_lora_str, text="Força do LoRA:").pack(side="left")
        self.cmb_lora_strength = ttk.Combobox(f_lora_str, values=["30", "40", "50", "60", "70", "80"], state="readonly", width=4)
        self.cmb_lora_strength.set("50")
        self.cmb_lora_strength.pack(side="left", padx=4)
        tk.Label(f_lora_str, text="30–60 mantém nitidez; acima de 80 pode dominar o prompt e borrar.",
                 anchor="w", fg="#777").pack(side="left", padx=8)

        # 4) pasta
        f3 = tk.Frame(root)
        f3.pack(fill="x", padx=14, pady=4)
        tk.Button(f3, text="3. Pasta de saída", width=22, command=self.escolher_pasta).pack(side="left")
        self.lbl_pasta = tk.Label(f3, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_pasta.pack(side="left", padx=8)

        # botão
        self.btn = tk.Button(root, text="GERAR RENDER", bg="#d2603a", fg="white",
                             font=("Segoe UI", 14, "bold"), height=2, command=self.gerar)
        self.btn.pack(fill="x", padx=14, pady=10)
        root.bind("<F5>", self._atalho_atualizar)

        # status + preview
        f_status = tk.Frame(root)
        f_status.pack(fill="x", padx=14)
        self.status = tk.Label(f_status, text="Pronto.", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        tk.Button(f_status, text="Destravar", command=self.destravar).pack(side="right")
        self.pbar = ttk.Progressbar(root, mode="indeterminate")
        self.pbar.pack(fill="x", padx=14, pady=4)
        self.lbl_tempo = tk.Label(root, text="", anchor="w", fg="#777")
        self.lbl_tempo.pack(fill="x", padx=14)
        self.preview = tk.Label(root)
        self.preview.pack(fill="both", expand=True, padx=14, pady=6)
        self.atualizar_motor()
        self.root.after(100, self.processar_fila)
        self.root.after(1000, self._tick_tempo)
        self.root.after(500, self.carregar_loras)

    def _tick_tempo(self):
        if self.gerando and self.tempo_inicio:
            segundos = int(time.time() - self.tempo_inicio)
            self.lbl_tempo.config(text=f"Em andamento: {segundos // 60:02d}:{segundos % 60:02d}")
        else:
            self.lbl_tempo.config(text="")
        self.root.after(1000, self._tick_tempo)

    def _reset_ui(self):
        self.gerando = False
        self.tempo_inicio = None
        try:
            self.pbar.stop()
            self.btn.config(state="normal")
        except Exception:
            pass

    def destravar(self):
        self.job_id += 1
        self._reset_ui()
        self.status.config(text="Interface destravada. Resultados da geração anterior serão ignorados.")
        logging.warning("Interface destravada manualmente; job_id=%s", self.job_id)

    def carregar_loras(self):
        self.btn_lora.config(state="disabled")
        self.lora_hint.config(text="Carregando a lista de LoRAs da conta...")
        threading.Thread(target=self._carregar_loras, daemon=True).start()

    def _carregar_loras(self):
        try:
            loras = ag.listar_loras()
            mapping = {"Nenhum (sem LoRA)": None}
            for item in loras:
                label = f'{item["name"]}  (ID {item["id"]})'
                mapping[label] = item["name"]
            self.fila_ui.put(("loras", list(mapping), mapping, None))
        except Exception as e:
            self.fila_ui.put(("loras", ["Nenhum (sem LoRA)"], {"Nenhum (sem LoRA)": None}, str(e)))

    def processar_fila(self):
        try:
            while True:
                item = self.fila_ui.get_nowait()
                tipo = item[0]
                try:
                    if tipo == "loras":
                        self._aplicar_loras(item[1], item[2], item[3])
                    elif tipo == "status":
                        if len(item) >= 3:
                            if item[1] != self.job_id:
                                continue
                            self.status.config(text=item[2])
                        else:
                            self.status.config(text=item[1])
                    elif tipo == "escolher":
                        if len(item) >= 5:
                            job_id, candidatos, meta_base, pasta = item[1], item[2], item[3], item[4]
                            if job_id != self.job_id:
                                continue
                            self._abrir_escolha(job_id, candidatos, meta_base, pasta)
                    elif tipo == "render_ok":
                        if len(item) >= 4:
                            job_id, jpg, nota = item[1], item[2], item[3]
                        else:
                            job_id, jpg, nota = self.job_id, item[1], ""
                        if job_id != self.job_id:
                            continue
                        self._finalizar_render_ok(jpg, nota)
                    elif tipo == "render_erro":
                        if len(item) >= 3:
                            job_id, erro = item[1], item[2]
                        else:
                            job_id, erro = self.job_id, item[1]
                        if job_id != self.job_id:
                            continue
                        self._finalizar_render_erro(erro)
                except Exception as e:
                    logging.exception("Erro ao processar item da fila: %r", item)
                    self.status.config(text=f"Erro interno na interface: {e}")
                    self._reset_ui()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.processar_fila)

    def _finalizar_render_ok(self, jpg, nota=""):
        try:
            self.status.config(text="Salvo: " + jpg)
            self.mostrar_preview(jpg)
        except Exception as e:
            logging.exception("Falha ao exibir preview: %s", e)
            self.status.config(text="Imagem salva, mas o preview falhou: " + str(e))
        finally:
            self._reset_ui()
        msg = "Cena salva em:\n" + jpg
        if nota:
            msg += "\n\n" + nota
        try:
            messagebox.showinfo("Pronto", msg)
        except Exception:
            logging.exception("Falha ao exibir mensagem de sucesso")

    def _finalizar_render_erro(self, erro):
        logging.error("Geração falhou: %s", erro)
        try:
            self.status.config(text="Erro: " + erro)
        finally:
            self._reset_ui()
        try:
            messagebox.showerror("Erro", erro)
        except Exception:
            logging.exception("Falha ao exibir mensagem de erro")

    def _aplicar_loras(self, labels, mapping, erro):
        atual = self.cmb_lora.get()
        self.lora_por_label = mapping
        self.cmb_lora.config(values=labels)
        if atual in mapping:
            self.cmb_lora.set(atual)
        else:
            self.cmb_lora.set("Nenhum (sem LoRA)")
        self.btn_lora.config(state="normal")
        self.lora_count = max(0, len(labels) - 1)
        if erro:
            self.lora_hint.config(text="LoRA: não consegui carregar a lista. Verifique a chave/Internet e clique em Atualizar.")
        else:
            self.atualizar_modo_lora()

    def atualizar_motor(self):
        motor = self.motor_map.get(self.cmb_motor.get(), "seedream")
        if motor == "seedream":
            self.cmb_estilo.config(state="disabled")
            self.cmb_engine.config(state="disabled")
            self.cmb_resolucao.config(values=["2k", "1.5k"])
            if self.cmb_resolucao.get() not in ("2k", "1.5k"):
                self.cmb_resolucao.set("2k")
        else:
            self.cmb_estilo.config(state="readonly")
            self.cmb_engine.config(state="readonly")
            self.cmb_resolucao.config(values=["2k", "4k"])
            if self.cmb_resolucao.get() not in ("2k", "4k"):
                self.cmb_resolucao.set("2k")
        self.atualizar_modo_lora()

    def atualizar_modo_lora(self):
        motor = self.motor_map.get(self.cmb_motor.get(), "seedream")
        if motor == "seedream":
            self.cmb_lora.config(state="disabled")
            self.lora_hint.config(
                text="Seedream preserva melhor a imagem base e não usa LoRA. Para usar LoRA, escolha o motor Mystic."
            )
        elif self.ref or self.ref_linhas:
            self.cmb_lora.config(state="disabled")
            self.lora_hint.config(
                text="Com referência de estilo ou linhas de lote, a API ignora LoRA. Remova essas imagens para usar LoRA."
            )
        else:
            self.cmb_lora.config(state="readonly")
            self.lora_hint.config(
                text=f"LoRA é estilo treinado; não é a imagem de referência. {self.lora_count} LoRA(s) encontrado(s)."
            )

    def _biblioteca_itens(self, modo="ref"):
        itens = []
        if REF_MANIFEST.exists():
            try:
                d = json.loads(REF_MANIFEST.read_text(encoding="utf-8"))
                for item in d.get("itens", []):
                    if not item.get("existe", True):
                        continue
                    if item.get("status") not in ("approved", "review"):
                        continue
                    p = REF_DIR / item.get("arquivo", "")
                    if not p.exists():
                        continue
                    tipo = item.get("tipo", "")
                    if modo == "ref" and tipo == "estrutura":
                        continue
                    if modo == "linhas" and tipo != "estrutura" and "loteamento" not in p.name.lower():
                        continue
                    itens.append({"path": p, "label": item.get("preset") or p.stem, "meta": f"{item.get('largura','?')}×{item.get('altura','?')} · {item.get('licenca','')}", "item": item})
            except Exception:
                logging.exception("Falha lendo manifesto de referências")
        if not itens:
            for p in sorted(REF_DIR.glob("*")):
                if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                    continue
                if modo == "ref" and ("antigo" in p.stem.lower() or "antiga" in p.stem.lower() or "soft" in p.stem.lower() or "ia_" in p.stem.lower() or "linha" in p.stem.lower()):
                    continue
                if modo == "linhas" and "linha" not in p.stem.lower() and "planta" not in p.stem.lower():
                    continue
                itens.append({"path": p, "label": p.stem, "meta": "arquivo local", "item": {}})
        return itens

    def abrir_biblioteca(self, modo="ref"):
        itens = self._biblioteca_itens(modo)
        top = tk.Toplevel(self.root)
        top.title("Biblioteca de referências" if modo == "ref" else "Biblioteca de linhas de lote")
        top.geometry("1120x620")
        top.transient(self.root)
        top.grab_set()
        tk.Label(top, text="Clique em uma miniatura para selecionar", font=("Segoe UI", 15, "bold")).pack(pady=10)
        grid = tk.Frame(top)
        grid.pack(fill="both", expand=True, padx=12, pady=4)
        self._gallery_thumbs = []
        for idx, info in enumerate(itens):
            try:
                im = Image.open(info["path"])
                im.thumbnail((240, 150), Image.Resampling.LANCZOS)
                ph = ImageTk.PhotoImage(im)
                self._gallery_thumbs.append(ph)
            except Exception:
                continue
            cell = tk.Frame(grid, bd=1, relief="solid", padx=5, pady=5)
            cell.grid(row=idx // 4, column=idx % 4, padx=8, pady=6, sticky="nsew")
            btn = tk.Button(cell, image=ph, bd=0, cursor="hand2",
                            command=lambda p=info["path"], t=top: self._selecionar_biblioteca(p, modo, t))
            btn.pack()
            tk.Label(cell, text=info["label"], font=("Segoe UI", 9, "bold"), wraplength=240).pack(pady=(4, 1))
            tk.Label(cell, text=info["meta"], font=("Segoe UI", 8), fg="#777").pack()
        for c in range(4):
            grid.columnconfigure(c, weight=1)
        if not itens:
            tk.Label(grid, text="Nenhuma referência ativa encontrada.", fg="#999").grid(row=0, column=0, pady=30)

    def _selecionar_biblioteca(self, caminho, modo, top):
        try:
            with Image.open(caminho) as im:
                w, h = im.size
            if modo == "ref":
                self.ref = str(caminho)
                self.lbl_ref.config(text=f"{caminho.name} ({w}x{h})")
                self.chk_agua.config(state="normal")
                self.status.config(text="Referência selecionada: " + caminho.name)
            else:
                self.ref_linhas = str(caminho)
                self.lbl_linhas.config(text=f"{caminho.name} ({w}x{h})")
                self.status.config(text="Linhas de lote selecionadas: " + caminho.name)
            self.atualizar_modo_lora()
            logging.info("BIBLIOTECA modo=%s arquivo=%s", modo, caminho)
        except Exception as e:
            messagebox.showerror("Referência inválida", str(e))
        finally:
            try:
                top.destroy()
            except Exception:
                pass

    def escolher_ref(self):
        p = filedialog.askopenfilename(title="Escolha a referência",
                                       filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if p:
            self.ref = p
            try:
                w, h = Image.open(p).size
            except Exception:
                w = h = 0
            aviso = " ⚠ baixa resolução" if min(w, h) and min(w, h) < 1024 else ""
            self.lbl_ref.config(text=f"{os.path.basename(p)} ({w}x{h}){aviso}")
            self.chk_agua.config(state="normal")
            if min(w, h) and min(w, h) < 1024:
                messagebox.showwarning(
                    "Referência pequena",
                    "Esta imagem tem menos de 1024 px no lado menor. Ela pode deixar o resultado mole ou tremido. "
                    "Prefira uma referência em alta resolução."
                )
            self.atualizar_modo_lora()

    def escolher_linhas(self):
        p = filedialog.askopenfilename(title="Escolha a planta com linhas de lote",
                                       filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if p:
            self.ref_linhas = p
            try:
                w, h = Image.open(p).size
            except Exception:
                w = h = 0
            self.lbl_linhas.config(text=f"{os.path.basename(p)} ({w}x{h})")
            self.atualizar_modo_lora()

    def limpar_ref(self):
        self.ref = ""
        self.lbl_ref.config(text="(nenhuma)")
        self.chk_agua.config(state="disabled")
        self.atualizar_modo_lora()
        self.status.config(text="Imagem de referência removida.")

    def limpar_linhas(self):
        self.ref_linhas = ""
        self.lbl_linhas.config(text="(nenhuma)")
        self.atualizar_modo_lora()
        self.status.config(text="Linhas de lote removidas.")

    @staticmethod
    def _imagem_ok(caminho):
        try:
            with Image.open(caminho) as im:
                im.verify()
            return True, ""
        except Exception as e:
            return False, str(e)

    def escolher_pasta(self):
        d = filedialog.askdirectory(title="Pasta de saída")
        if d:
            self.pasta = d
            self.lbl_pasta.config(text=d)

    @staticmethod
    def _limpar_prompt(prompt):
        """Remove bloco de negativo colado por engano; Mystic não aceita negativo."""
        for marca in ("NEGATIVE PROMPT", "--- NEGATIVE / NEGATIVO ---", "NEGATIVO"):
            i = prompt.find(marca)
            if i != -1:
                return prompt[:i].strip()
        return prompt

    def _atalho_atualizar(self, event=None):
        """F5 atualiza a interface e recarrega os dados da conta."""
        self.status.config(text="Atualizando interface e lista de LoRAs...")
        self.atualizar_motor()
        self.carregar_loras()
        return "break"

    def gerar(self):
        if self.gerando:
            self.status.config(text="Já existe uma geração em andamento. Use Destravar se quiser liberar a interface.")
            return

        prompt = self.txt_prompt.get("1.0", "end").strip()
        prompt_limpo = self._limpar_prompt(prompt)
        if prompt_limpo != prompt:
            prompt = prompt_limpo
            messagebox.showinfo(
                "Prompt ajustado",
                "Removi o bloco de prompt negativo. O Mystic não tem campo de negativo; "
                "quando esse texto é colado junto, ele vira parte do pedido e pode deixar a imagem ruim."
            )
        if not prompt:
            messagebox.showwarning("Falta", "O prompt está vazio.")
            return
        if not self.pasta:
            messagebox.showwarning("Falta", "Escolha a pasta de saída.")
            return
        if not os.path.isdir(self.pasta):
            messagebox.showerror("Pasta inválida", "A pasta de saída não existe ou não está acessível.")
            return
        if self.ref:
            ok, erro = self._imagem_ok(self.ref)
            if not ok:
                messagebox.showerror("Referência inválida", "A imagem de referência não pôde ser lida:\n" + erro)
                self.limpar_ref()
                return
        if self.ref_linhas:
            ok, erro = self._imagem_ok(self.ref_linhas)
            if not ok:
                messagebox.showerror("Linhas inválidas", "A planta de linhas não pôde ser lida:\n" + erro)
                self.limpar_linhas()
                return
        motor = self.motor_map.get(self.cmb_motor.get(), "mystic")
        if motor == "seedream" and not self.ref:
            messagebox.showwarning("Falta", "O motor Seedream precisa de uma imagem de referência.")
            return
        if not self.ref:
            msg_sem_ref = (
                "Você não selecionou uma imagem de referência de estilo.\n\n"
                "Sem ela, o Mystic vai inventar a cena e o resultado pode não seguir o prompt."
            )
            lora_sel = self.lora_por_label.get(self.cmb_lora.get())
            if lora_sel:
                msg_sem_ref += (
                    f"\n\nLoRA selecionado: {lora_sel}.\n"
                    "Sem referência, o LoRA pode puxar a cena para outro estilo e ignorar parte do prompt."
                )
            msg_sem_ref += "\n\nDeseja continuar mesmo assim?"
            if not messagebox.askyesno("Sem imagem de referência", msg_sem_ref):
                self.status.config(text="Geração cancelada: nenhuma imagem de referência selecionada.")
                return
        style_ref_path = self.ref or None
        structure_path = self.ref_linhas or None
        if motor == "seedream" and structure_path:
            messagebox.showwarning(
                "Linhas de lote no Mystic",
                "O Seedream não usa a referência de estrutura. Para preservar as linhas de lote, use o motor Mystic."
            )
            return
        lora_name = None if style_ref_path or structure_path or motor == "seedream" else self.lora_por_label.get(self.cmb_lora.get())
        lora_strength = int(self.cmb_lora_strength.get() or 50)
        engine = self.engine_map.get(self.cmb_engine.get(), "magnific_sharpy")
        resolution = self.cmb_resolucao.get()
        aspecto = self.cmb_aspect.get()
        estilo = self.cmb_estilo.get()
        pasta = self.pasta
        ref_image = self.ref or None
        modo_qualidade = self.modo_qualidade.get()
        fixar_geracao = self.fixar_geracao.get()
        if fixar_geracao and modo_qualidade:
            modo_qualidade = False
            self.status.config(text="Geração fixa ativa: gerando 1 versão.")
        checar_conteudo = self.checar_conteudo.get()
        escolher_manual = self.escolher_manual.get()
        prompt_geracao = prompt
        cena_tem_agua = any(t in prompt.lower() for t in (
            "lake", "lago", "lagoa", "water", "água", "agua", "pool", "piscina", "espelho"
        ))
        if self.nao_expandir_agua.get() and self.ref and cena_tem_agua:
            prompt_geracao += (
                "\n\nCONTROLE DE ÁGUA\nManter lagos, lagoas e espelhos d'água exatamente no contorno, "
                "área e posição da imagem de referência. Não ampliar nem criar novos corpos d'água. "
                "A água só pode existir dentro das áreas já desenhadas."
            )
        if motor == "seedream":
            sufixo = " com Seedream 5 Pro Edit"
        elif style_ref_path and structure_path:
            sufixo = " com referência de estilo + linhas de lote"
        elif style_ref_path:
            sufixo = " com referência de estilo"
        elif lora_name:
            sufixo = " com LoRA " + lora_name
        else:
            sufixo = ""
        self.job_id += 1
        job_id = self.job_id
        self.gerando = True
        self.tempo_inicio = time.time()
        self.status.config(text="Gerando no Magnific" + sufixo + "...")
        self.btn.config(state="disabled")
        self.pbar.start(10)
        logging.info(
            "INICIO job=%s motor=%s estilo=%s engine=%s res=%s aspecto=%s lora=%s forca=%s ref=%s linhas=%s qualidade=%s fixa=%s checagem=%s pasta=%s",
            job_id, motor, estilo, engine, resolution, aspecto, lora_name, lora_strength,
            style_ref_path, structure_path, modo_qualidade, fixar_geracao, checar_conteudo, pasta,
        )
        threading.Thread(
            target=self._gerar,
            args=(prompt_geracao, motor, lora_name, lora_strength, style_ref_path, structure_path,
                  engine, resolution, aspecto, ref_image, modo_qualidade, checar_conteudo,
                  job_id, pasta, estilo, fixar_geracao, escolher_manual),
            daemon=True,
        ).start()

    @staticmethod
    def _agua_indevida(prompt, descricao):
        """Detecta água inventada quando o prompt não pediu água."""
        termos = (
            "water", "pool", "lake", "pond", "lagoon", "ocean", "river",
            "submerged", "piscina", "lago", "lagoa", "água", "agua",
            "espelho d'água", "espelho d agua",
        )
        p = (prompt or "").lower()
        d = (descricao or "").lower()
        for neg in (
            "no water or reflective pool under the court", "no reflective pool",
            "no water", "no pool", "no lake", "sem água", "sem agua",
            "sem lago", "sem piscina",
        ):
            p = p.replace(neg, " ")
        if any(t in p for t in termos):
            return False
        return any(t in d for t in termos)

    @staticmethod
    def _nitidez(caminho):
        try:
            import numpy as np
            im = Image.open(caminho).convert("L")
            im.thumbnail((1024, 1024))
            a = np.asarray(im, dtype=np.float32)
            lap = (-4 * a[1:-1, 1:-1] + a[:-2, 1:-1] + a[2:, 1:-1]
                   + a[1:-1, :-2] + a[1:-1, 2:])
            return float(lap.var())
        except Exception:
            return 0.0

    def _gerar_candidato(self, prompt, motor, lora_name, lora_strength, style_ref_path,
                         structure_path, engine, resolution, aspecto, ref_image,
                         pasta, estilo, versao, fixar_geracao):
        if motor == "seedream":
            res_seedream = "1.5k" if resolution == "1k" else "2k"
            task_id = ag.gerar_no_seedream_edit(
                prompt,
                aspecto,
                reference_path=ref_image,
                resolution=res_seedream,
                thinking_level="high",
                seed=12345 + versao,
            )
        else:
            task_id = ag.gerar_no_magnific(
                prompt,
                aspecto,
                estilo,
                structure_path=structure_path,
                structure_strength=95,
                style_reference_path=style_ref_path,
                adherence=45,
                hdr=30,
                lora_name=lora_name,
                lora_strength=lora_strength,
                engine=engine,
                resolution=resolution,
                creative_detailing=38 if lora_name else 28,
                fixed_generation=fixar_geracao,
            )
        logging.info("TASK job_versao=%s motor=%s task_id=%s", versao, motor, task_id)
        modelo_aguardar = "text-to-image/seedream-v5-pro-edit" if motor == "seedream" else "mystic"
        url = ag.aguardar(task_id, modelo=modelo_aguardar)
        if not url:
            raise RuntimeError("sem URL de resultado")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp = os.path.join(pasta, f"cena_{stamp}_v{versao}.png")
        jpg = os.path.join(pasta, f"cena_{stamp}_v{versao}.jpg")
        ag.baixar(url, tmp)
        im = Image.open(tmp).convert("RGB")
        im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=90, threshold=3))
        im.save(jpg, "JPEG", quality=95, optimize=True)
        try:
            os.remove(tmp)
        except OSError:
            pass
        score = self._nitidez(jpg)
        logging.info("CANDIDATO v%s nitidez=%.2f arquivo=%s", versao, score, jpg)
        return {"arquivo": jpg, "task_id": task_id, "url": url, "nitidez": score}

    def _abrir_escolha(self, job_id, candidatos, meta_base, pasta):
        if job_id != self.job_id:
            return
        top = tk.Toplevel(self.root)
        top.title("Escolher a melhor versão")
        top.geometry("1040x700")
        top.transient(self.root)
        top.grab_set()
        self.janela_escolha = top
        self._thumbs = []
        tk.Label(top, text="Qual versão deve ser mantida?", font=("Segoe UI", 15, "bold")).pack(pady=10)
        frame = tk.Frame(top)
        frame.pack(fill="both", expand=True, padx=12, pady=4)
        for i, cand in enumerate(candidatos):
            col = tk.Frame(frame)
            col.pack(side="left", expand=True, fill="both", padx=8)
            im = Image.open(cand["arquivo"])
            im.thumbnail((460, 330))
            ph = ImageTk.PhotoImage(im)
            self._thumbs.append(ph)
            tk.Label(col, image=ph).pack(pady=4)
            flag = " · ÁGUA INDEVIDA" if cand.get("agua_indevida") else ""
            tk.Label(col, text=f"Versão {i + 1} · nitidez {cand['nitidez']:.0f}{flag}", font=("Segoe UI", 10)).pack(pady=3)
            tk.Button(col, text=f"Usar versão {i + 1}", height=2,
                      command=lambda idx=i: self._aplicar_escolha(job_id, candidatos, meta_base, pasta, idx)).pack(fill="x", pady=6)
        def fechar():
            melhor = min(range(len(candidatos)), key=lambda i: (bool(candidatos[i].get("agua_indevida")), -float(candidatos[i]["nitidez"])))
            self._aplicar_escolha(job_id, candidatos, meta_base, pasta, melhor)
        top.protocol("WM_DELETE_WINDOW", fechar)

    def _aplicar_escolha(self, job_id, candidatos, meta_base, pasta, idx):
        if job_id != self.job_id:
            return
        try:
            if hasattr(self, "janela_escolha") and self.janela_escolha.winfo_exists():
                self.janela_escolha.destroy()
        except Exception:
            pass
        try:
            escolhido = candidatos[idx]
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_jpg = os.path.join(pasta, f"cena_{stamp}.jpg")
            os.replace(escolhido["arquivo"], final_jpg)
            escolhido["arquivo"] = final_jpg
            alt_jpg = None
            for i, cand in enumerate(candidatos):
                if i == idx:
                    continue
                alt_jpg = os.path.join(pasta, f"cena_{stamp}_alternativa.jpg")
                os.replace(cand["arquivo"], alt_jpg)
                cand["arquivo"] = alt_jpg
                break
            meta = dict(meta_base)
            meta.update({"candidatos": candidatos, "arquivo_final": final_jpg, "arquivo_alternativo": alt_jpg, "escolha_manual": True})
            with open(os.path.join(pasta, f"cena_{stamp}.json"), "w", encoding="utf-8") as f:
                import json
                json.dump(meta, f, ensure_ascii=False, indent=2)
            nota = f"Versão {idx + 1} escolhida manualmente."
            if alt_jpg:
                nota += f"\nAlternativa salva em: {alt_jpg}"
            logging.info("ESCOLHA MANUAL job=%s versao=%s arquivo=%s", job_id, idx + 1, final_jpg)
            self._finalizar_render_ok(final_jpg, nota)
        except Exception as e:
            logging.exception("Falha ao aplicar escolha manual")
            self._finalizar_render_erro(str(e))

    def _gerar(self, prompt, motor, lora_name, lora_strength, style_ref_path, structure_path,
               engine, resolution, aspecto, ref_image, modo_qualidade, checar_conteudo,
               job_id, pasta, estilo, fixar_geracao, escolher_manual):
        try:
            total = 2 if modo_qualidade else 1
            candidatos = []
            erros = []
            for i in range(1, total + 1):
                if job_id != self.job_id:
                    logging.info("Job %s cancelado antes da versão %s", job_id, i)
                    return
                self.fila_ui.put(("status", job_id, f"Gerando versão {i}/{total}..."))
                try:
                    cand = self._gerar_candidato(
                        prompt, motor, lora_name, lora_strength, style_ref_path, structure_path,
                        engine, resolution, aspecto, ref_image, pasta, estilo, i, fixar_geracao)
                    cand["descricao"] = ""
                    cand["agua_indevida"] = False
                    cand["erro_conteudo"] = None
                    if checar_conteudo:
                        self.fila_ui.put(("status", job_id, f"Conferindo conteúdo da versão {i}/{total}..."))
                        try:
                            cand["descricao"] = ag.gerar_prompt_por_imagem(cand["arquivo"], timeout_s=180)
                            cand["agua_indevida"] = self._agua_indevida(prompt, cand["descricao"])
                            logging.info("CONTEUDO v%s agua_indevida=%s", i, cand["agua_indevida"])
                        except Exception as e:
                            cand["erro_conteudo"] = str(e)
                            logging.warning("Falha na checagem de conteúdo v%s: %s", i, e)
                    candidatos.append(cand)
                except Exception as e:
                    erros.append(str(e))
                    logging.exception("Versão %s falhou", i)
                    self.fila_ui.put(("status", job_id, f"Versão {i} falhou: {e}"))
            if job_id != self.job_id:
                logging.info("Job %s cancelado antes de salvar", job_id)
                return
            if not candidatos:
                raise RuntimeError("; ".join(erros) if erros else "nenhuma versão gerada")
            meta_base = {
                "data": datetime.now().isoformat(timespec="seconds"),
                "motor": motor,
                "estilo": estilo,
                "engine": engine,
                "resolucao": resolution,
                "aspecto": aspecto,
                "lora": lora_name,
                "lora_strength": lora_strength if lora_name else None,
                "referencia": style_ref_path or ref_image,
                "estrutura_linhas": structure_path,
                "modo_qualidade": modo_qualidade,
                "checagem_conteudo": checar_conteudo,
                "fixed_generation": fixar_geracao,
                "prompt": prompt,
            }
            if escolher_manual and len(candidatos) > 1:
                logging.info("Aguardando escolha manual job=%s", job_id)
                self.fila_ui.put(("escolher", job_id, candidatos, meta_base, pasta))
                return
            candidatos.sort(key=lambda x: (bool(x.get("agua_indevida")), -float(x["nitidez"])))
            melhor = candidatos[0]
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_jpg = os.path.join(pasta, f"cena_{stamp}.jpg")
            os.replace(melhor["arquivo"], final_jpg)
            melhor["arquivo"] = final_jpg
            alt_jpg = None
            if len(candidatos) > 1:
                alt_jpg = os.path.join(pasta, f"cena_{stamp}_alternativa.jpg")
                os.replace(candidatos[1]["arquivo"], alt_jpg)
                candidatos[1]["arquivo"] = alt_jpg
            meta = dict(meta_base)
            meta.update({"candidatos": candidatos, "arquivo_final": final_jpg, "arquivo_alternativo": alt_jpg})
            with open(os.path.join(pasta, f"cena_{stamp}.json"), "w", encoding="utf-8") as f:
                import json
                json.dump(meta, f, ensure_ascii=False, indent=2)
            nota = f"Nitidez escolhida: {melhor['nitidez']:.1f}"
            if melhor.get("agua_indevida"):
                nota += "\nAtenção: a checagem detectou água indevida nesta versão."
            if alt_jpg:
                nota += f"\nAlternativa salva em: {alt_jpg}"
            logging.info("FIM job=%s arquivo=%s nitidez=%.2f alt=%s", job_id, final_jpg, melhor["nitidez"], alt_jpg)
            self.fila_ui.put(("render_ok", job_id, final_jpg, nota))
        except Exception as e:
            logging.exception("ERRO job=%s", job_id)
            self.fila_ui.put(("render_erro", job_id, str(e)))

    def mostrar_preview(self, jpg):
        im = Image.open(jpg)
        im.thumbnail((420, 300))
        self.foto = ImageTk.PhotoImage(im)
        self.preview.config(image=self.foto)


if __name__ == "__main__":
    raiz = tk.Tk()
    try:
        raiz.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), "GR.ico"))
    except Exception:
        pass
    App(raiz)
    raiz.mainloop()


