#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeraPrompt Render â€” GUI separada (gerador de CENAS 3D via API do Magnific).
NÃ£o tem vÃ­nculo com o GeraPrompt HTML.
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


PROMPT_PADRAO = ("aerial hyperrealist photograph of a high-end tropical gated community, with royal palms, "
                 "ixora flower beds, manicured lawn, golden hour, photorealistic, 8k")


class App:
    def __init__(self, root):
        self.root = root
        root.title("GeraPrompt Render â€” gerar cena")
        root.geometry("760x700")
        self.ref = ""
        self.pasta = ""
        self.foto = None

        # 1) referÃªncia
        f1 = tk.Frame(root)
        f1.pack(fill="x", padx=14, pady=8)
        tk.Button(f1, text="1. Imagem de referÃªncia", width=22, command=self.escolher_ref).pack(side="left")
        self.lbl_ref = tk.Label(f1, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_ref.pack(side="left", padx=8)

        # 2) prompt
        tk.Label(root, text="2. Prompt (cole o do GeraPrompt ou digite):", anchor="w").pack(fill="x", padx=14)
        self.txt_prompt = tk.Text(root, height=8, font=("Consolas", 9))
        self.txt_prompt.pack(fill="both", padx=14, pady=4)
        self.txt_prompt.insert("end", PROMPT_PADRAO)

        # 3) opÃ§Ãµes
        f2 = tk.Frame(root)
        f2.pack(fill="x", padx=14, pady=4)
        tk.Label(f2, text="ProporÃ§Ã£o:").pack(side="left")
        self.cmb_aspect = ttk.Combobox(f2, values=["16:9", "1:1", "4:3", "3:4", "9:16", "3:2"], width=8)
        self.cmb_aspect.set("16:9")
        self.cmb_aspect.pack(side="left", padx=4)
        tk.Label(f2, text="Estilo:").pack(side="left", padx=(14, 0))
        self.cmb_estilo = ttk.Combobox(f2, values=["super_real", "realism", "fluid", "zen", "flexible"], width=12)
        self.cmb_estilo.set("super_real")
        self.cmb_estilo.pack(side="left", padx=4)

        # 4) pasta
        f3 = tk.Frame(root)
        f3.pack(fill="x", padx=14, pady=4)
        tk.Button(f3, text="3. Pasta de saÃ­da", width=22, command=self.escolher_pasta).pack(side="left")
        self.lbl_pasta = tk.Label(f3, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_pasta.pack(side="left", padx=8)

        # botÃ£o
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

    def escolher_ref(self):
        p = filedialog.askopenfilename(title="Escolha a referÃªncia",
                                       filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos", "*.*")])
        if p:
            self.ref = p
            self.lbl_ref.config(text=os.path.basename(p))

    def escolher_pasta(self):
        d = filedialog.askdirectory(title="Pasta de saÃ­da")
        if d:
            self.pasta = d
            self.lbl_pasta.config(text=d)

    def gerar(self):
        prompt = self.txt_prompt.get("1.0", "end").strip()
        if not prompt:
            messagebox.showwarning("Falta", "O prompt estÃ¡ vazio.")
            return
        if not self.pasta:
            messagebox.showwarning("Falta", "Escolha a pasta de saÃ­da.")
            return
        self.btn.config(state="disabled")
        self.pbar.start(10)
        threading.Thread(target=self._gerar, args=(prompt,), daemon=True).start()

    def _gerar(self, prompt):
        try:
            image_url = None
            if self.ref and os.path.exists(self.ref):
                self.status.config(text="Enviando a referÃªncia...")
                image_url = ag.upload_imagem(self.ref)
            self.status.config(text="Gerando no Magnific...")
            task_id = ag.gerar_no_magnific(prompt, self.cmb_aspect.get(), self.cmb_estilo.get(), image_url)
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


