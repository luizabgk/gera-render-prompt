#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeraPrompt Render — GUI separada (gerador de CENAS 3D via API do Magnific).
Não tem vínculo com o GeraPrompt HTML.
"""
import os
import queue
import sys
import threading
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geraprompt_agente as ag

ag.API_KEY = os.environ.get('MAGNIFIC_API_KEY', ag.API_KEY).strip() or ag.API_KEY


PROMPT_PADRAO = ""


class App:
    def __init__(self, root):
        self.root = root
        root.title("GeraPrompt Render — gerar cena")
        root.geometry("900x860")
        self.ref = ""
        self.ref_linhas = ""
        self.pasta = ""
        self.foto = None
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
        self.modo_qualidade = tk.BooleanVar(value=True)

        # 1) referência
        f1 = tk.Frame(root)
        f1.pack(fill="x", padx=14, pady=8)
        tk.Button(f1, text="1. Imagem de referência (estilo)", width=26, command=self.escolher_ref).pack(side="left")
        self.lbl_ref = tk.Label(f1, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_ref.pack(side="left", padx=8)
        tk.Label(root, text="A imagem de referência entra como estilo no Mystic; não é estrutura de planta.",
                 anchor="w", fg="#777").pack(fill="x", padx=14)
        f1b = tk.Frame(root)
        f1b.pack(fill="x", padx=14, pady=(0, 4))
        tk.Button(f1b, text="1b. Linhas de lote (opcional)", width=26, command=self.escolher_linhas).pack(side="left")
        self.lbl_linhas = tk.Label(f1b, text="(nenhuma)", anchor="w", fg="#333")
        self.lbl_linhas.pack(side="left", padx=8)
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
        self.status = tk.Label(root, text="Pronto.", anchor="w")
        self.status.pack(fill="x", padx=14)
        self.pbar = ttk.Progressbar(root, mode="indeterminate")
        self.pbar.pack(fill="x", padx=14, pady=4)
        self.preview = tk.Label(root)
        self.preview.pack(fill="both", expand=True, padx=14, pady=6)
        self.atualizar_motor()
        self.root.after(100, self.processar_fila)
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
                mapping[label] = item["name"]
            self.fila_ui.put(("loras", list(mapping), mapping, None))
        except Exception as e:
            self.fila_ui.put(("loras", ["Nenhum (sem LoRA)"], {"Nenhum (sem LoRA)": None}, str(e)))

    def processar_fila(self):
        try:
            while True:
                item = self.fila_ui.get_nowait()
                tipo = item[0]
                if tipo == "loras":
                    self._aplicar_loras(item[1], item[2], item[3])
                elif tipo == "status":
                    self.status.config(text=item[1])
                elif tipo == "render_ok":
                    self._finalizar_render_ok(item[1], item[2] if len(item) > 2 else "")
                elif tipo == "render_erro":
                    self._finalizar_render_erro(item[1])
        except queue.Empty:
            pass
        self.root.after(100, self.processar_fila)

    def _finalizar_render_ok(self, jpg, nota=""):
        self.status.config(text="Salvo: " + jpg)
        self.mostrar_preview(jpg)
        self.pbar.stop()
        self.btn.config(state="normal")
        msg = "Cena salva em:\n" + jpg
        if nota:
            msg += "\n\n" + nota
        messagebox.showinfo("Pronto", msg)

    def _finalizar_render_erro(self, erro):
        self.status.config(text="Erro: " + erro)
        self.pbar.stop()
        self.btn.config(state="normal")
        messagebox.showerror("Erro", erro)

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
        self.status.config(text="Gerando no Magnific" + sufixo + "...")
        self.btn.config(state="disabled")
        self.pbar.start(10)
        threading.Thread(
            target=self._gerar,
            args=(prompt_geracao, motor, lora_name, lora_strength, style_ref_path, structure_path,
                  engine, resolution, aspecto, self.ref or None, self.modo_qualidade.get()),
            daemon=True,
        ).start()

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

    def _gerar_candidato(self, prompt, motor, lora_name, lora_strength, style_ref_path, structure_path,
                         engine, resolution, aspecto, ref_image, versao):
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
                self.cmb_estilo.get(),
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
            )
        modelo_aguardar = "text-to-image/seedream-v5-pro-edit" if motor == "seedream" else "mystic"
        url = ag.aguardar(task_id, modelo=modelo_aguardar)
        if not url:
            raise RuntimeError("sem URL de resultado")
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tmp = os.path.join(self.pasta, f"cena_{stamp}_v{versao}.png")
        jpg = os.path.join(self.pasta, f"cena_{stamp}_v{versao}.jpg")
        ag.baixar(url, tmp)
        im = Image.open(tmp).convert("RGB")
        im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=90, threshold=3))
        im.save(jpg, "JPEG", quality=95, optimize=True)
        try:
            os.remove(tmp)
        except OSError:
            pass
        score = self._nitidez(jpg)
        return {"arquivo": jpg, "task_id": task_id, "url": url, "nitidez": score}

    def _gerar(self, prompt, motor, lora_name, lora_strength, style_ref_path, structure_path,
               engine, resolution, aspecto, ref_image, modo_qualidade):
        try:
            total = 2 if modo_qualidade else 1
            candidatos = []
            erros = []
            for i in range(1, total + 1):
                self.fila_ui.put(("status", f"Gerando versão {i}/{total}..."))
                try:
                    candidatos.append(self._gerar_candidato(
                        prompt, motor, lora_name, lora_strength, style_ref_path, structure_path,
                        engine, resolution, aspecto, ref_image, i))
                except Exception as e:
                    erros.append(str(e))
                    self.fila_ui.put(("status", f"Versão {i} falhou: {e}"))
            if not candidatos:
                raise RuntimeError("; ".join(erros) if erros else "nenhuma versão gerada")
            candidatos.sort(key=lambda x: x["nitidez"], reverse=True)
            melhor = candidatos[0]
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_jpg = os.path.join(self.pasta, f"cena_{stamp}.jpg")
            os.replace(melhor["arquivo"], final_jpg)
            # salva a alternativa, se existir
            alt_jpg = None
            if len(candidatos) > 1:
                alt_jpg = os.path.join(self.pasta, f"cena_{stamp}_alternativa.jpg")
                os.replace(candidatos[1]["arquivo"], alt_jpg)
            meta = {
                "data": datetime.now().isoformat(timespec="seconds"),
                "motor": motor,
                "estilo": self.cmb_estilo.get(),
                "engine": engine,
                "resolucao": resolution,
                "aspecto": aspecto,
                "lora": lora_name,
                "lora_strength": lora_strength if lora_name else None,
                "referencia": style_ref_path or ref_image,
                "estrutura_linhas": structure_path,
                "modo_qualidade": modo_qualidade,
                "prompt": prompt,
                "candidatos": candidatos,
                "arquivo_final": final_jpg,
                "arquivo_alternativo": alt_jpg,
            }
            with open(os.path.join(self.pasta, f"cena_{stamp}.json"), "w", encoding="utf-8") as f:
                import json
                json.dump(meta, f, ensure_ascii=False, indent=2)
            nota = f"Nitidez escolhida: {melhor['nitidez']:.1f}"
            if alt_jpg:
                nota += f"\nAlternativa salva em: {alt_jpg}"
            self.fila_ui.put(("render_ok", final_jpg, nota))
        except Exception as e:
            self.fila_ui.put(("render_erro", str(e)))

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


