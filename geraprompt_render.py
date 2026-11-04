#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeraPrompt Render — GUI separada (gerador de CENAS 3D via API do Magnific).
Não tem vínculo com o GeraPrompt HTML.
"""
import os
import sys
import threading
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geraprompt_agente as ag

ag.API_KEY = os.environ.get('MAGNIFIC_API_KEY', ag.API_KEY).strip() or ag.API_KEY


PROMPT_PADRAO = ""


class App:
    def __init__(self, root):
        self.root = root
        root.title("GeraPrompt Render — gerar cena")
        root.geometry("820x810")
        self.ref = ""
        self.pasta = ""
        self.foto = None
        self.lora_por_label = {"Nenhum (sem LoRA)": None}
        self.usar_estrutura = tk.BooleanVar(value=True)
        self.engine_map = {
            "Sharpy (foto/arquitetura)": "magnific_sharpy",
            "Automático": "automatic",
            "Sparkle (realista intermediário)": "magnific_sparkle",
            "Illusio (ilustração/natureza)": "magnific_illusio",
        }
        self.lora_count = 0

        # 1) referência
        f1 = tk.Frame(root)
        f1.pack(fill="x", padx=14, pady=8)
        tk.Button(f1, text="1. Imagem de referência", width=22, command=self.escolher_ref).pack(side="left")
        self.lbl_ref = tk.Label(f1, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_ref.pack(side="left", padx=8)
        self.btn_prompt_img = tk.Button(f1, text="Gerar prompt pela imagem", command=self.gerar_prompt_imagem)
        self.btn_prompt_img.pack(side="right")
        self.chk_estrutura = tk.Checkbutton(
            root,
            text="Usar imagem como estrutura (recomendado para preservar o traçado)",
            variable=self.usar_estrutura,
            command=self.atualizar_modo_lora,
        )
        self.chk_estrutura.pack(fill="x", padx=14)

        # 2) prompt
        tk.Label(root, text="2. Prompt (cole o do GeraPrompt ou digite):", anchor="w").pack(fill="x", padx=14)
        self.txt_prompt = tk.Text(root, height=8, font=("Consolas", 9))
        self.txt_prompt.pack(fill="both", padx=14, pady=4)
        self.txt_prompt.insert("end", PROMPT_PADRAO)
        tk.Label(root, text="Cole o prompt do GeraPrompt ou use o botão de análise da imagem (consome créditos).",
                 anchor="w", fg="#666").pack(fill="x", padx=14)

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
        self.cmb_resolucao = ttk.Combobox(f_opts2, values=["1k", "2k", "4k"], state="readonly", width=5)
        self.cmb_resolucao.set("2k")
        self.cmb_resolucao.pack(side="left", padx=4)

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

        # status + preview
        self.status = tk.Label(root, text="Pronto.", anchor="w")
        self.status.pack(fill="x", padx=14)
        self.pbar = ttk.Progressbar(root, mode="indeterminate")
        self.pbar.pack(fill="x", padx=14, pady=4)
        self.preview = tk.Label(root)
        self.preview.pack(fill="both", expand=True, padx=14, pady=6)
        self.root.after(500, self.carregar_loras)

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
                mapping[label] = item["id"]
            labels = list(mapping)
            self.root.after(0, self._aplicar_loras, labels, mapping, None)
        except Exception as e:
            self.root.after(0, self._aplicar_loras, ["Nenhum (sem LoRA)"], {"Nenhum (sem LoRA)": None}, str(e))

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

    def atualizar_modo_lora(self):
        if self.ref and self.usar_estrutura.get():
            self.cmb_lora.config(state="disabled")
            self.lora_hint.config(
                text="Com imagem como estrutura, a API ignora LoRA. O LoRA fica disponível ao desmarcar a opção acima."
            )
        else:
            self.cmb_lora.config(state="readonly")
            self.lora_hint.config(
                text=f"LoRA é estilo treinado; não é a imagem de referência. {self.lora_count} LoRA(s) encontrado(s)."
            )

    def escolher_ref(self):
        p = filedialog.askopenfilename(title="Escolha a referência",
                                       filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if p:
            self.ref = p
            self.lbl_ref.config(text=os.path.basename(p))
            self.atualizar_modo_lora()

    def escolher_pasta(self):
        d = filedialog.askdirectory(title="Pasta de saída")
        if d:
            self.pasta = d
            self.lbl_pasta.config(text=d)

    def gerar_prompt_imagem(self):
        if not self.ref:
            messagebox.showwarning("Falta", "Escolha primeiro uma imagem de referência.")
            return
        atual = self.txt_prompt.get("1.0", "end").strip()
        if atual and not messagebox.askyesno("Substituir prompt?", "Isso vai substituir o prompt atual. Continuar?"):
            return
        self.btn_prompt_img.config(state="disabled")
        self.pbar.start(10)
        self.status.config(text="Analisando a imagem no Magnific...")
        threading.Thread(target=self._gerar_prompt_imagem, daemon=True).start()

    def _gerar_prompt_imagem(self):
        try:
            prompt = ag.gerar_prompt_por_imagem(self.ref)
            self.txt_prompt.delete("1.0", "end")
            self.txt_prompt.insert("end", prompt)
            self.status.config(text=f"Prompt gerado pela imagem ({len(prompt)} caracteres).")
            messagebox.showinfo("Prompt gerado", "O prompt descritivo foi colocado no campo de texto. Revise antes de gerar.")
        except Exception as e:
            self.status.config(text="Erro: " + str(e))
            messagebox.showerror("Erro", str(e))
        finally:
            self.pbar.stop()
            self.btn_prompt_img.config(state="normal")

    def gerar(self):
        prompt = self.txt_prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Falta", "O prompt está vazio.")
            return
        if not self.pasta:
            messagebox.showwarning("Falta", "Escolha a pasta de saída.")
            return
        usar_estrutura = bool(self.ref) and self.usar_estrutura.get()
        structure_path = self.ref if usar_estrutura else None
        lora_name = None if usar_estrutura else self.lora_por_label.get(self.cmb_lora.get())
        engine = self.engine_map.get(self.cmb_engine.get(), "magnific_sharpy")
        resolution = self.cmb_resolucao.get()
        self.btn.config(state="disabled")
        self.pbar.start(10)
        threading.Thread(
            target=self._gerar,
            args=(prompt, lora_name, structure_path, engine, resolution),
            daemon=True,
        ).start()

    def _gerar(self, prompt, lora_name, structure_path, engine, resolution):
        try:
            if structure_path:
                sufixo = " com estrutura da imagem"
            elif lora_name:
                sufixo = " com LoRA " + lora_name
            else:
                sufixo = ""
            self.status.config(text="Gerando no Magnific" + sufixo + "...")
            task_id = ag.gerar_no_magnific(
                prompt,
                self.cmb_aspect.get(),
                self.cmb_estilo.get(),
                structure_path=structure_path,
                structure_strength=90,
                lora_name=lora_name,
                engine=engine,
                resolution=resolution,
            )
            url = ag.aguardar(task_id)
            if not url:
                raise RuntimeError("sem URL de resultado")
            nome = "cena_" + datetime.now().strftime("%Y%m%d_%H%M%S")
            tmp = os.path.join(self.pasta, nome + ".png")
            jpg = os.path.join(self.pasta, nome + ".jpg")
            ag.baixar(url, tmp)
            Image.open(tmp).convert("RGB").save(jpg, "JPEG", quality=95)
            try:
                os.remove(tmp)
            except OSError:
                pass
            self.status.config(text="Salvo: " + jpg)
            self.mostrar_preview(jpg)
            messagebox.showinfo("Pronto", "Cena salva em:\n" + jpg)
        except Exception as e:
            self.status.config(text="Erro: " + str(e))
            messagebox.showerror("Erro", str(e))
        finally:
            self.pbar.stop()
            self.btn.config(state="normal")

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


