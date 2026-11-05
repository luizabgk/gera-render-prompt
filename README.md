# GeraPrompt Render

Aplicativo desktop para gerar **cenas 3D, perspectivas e conceitos** de arquitetura e urbanismo com a API do [Magnific](https://www.magnific.com), usando uma imagem de referência e um prompt do GeraPrompt.

- **GeraPrompt (HTML):** monta o prompt e organiza as referências.
- **GeraPrompt Render (este app):** recebe o prompt, a referência de estilo e, quando necessário, a planta de linhas de lote.

Os dois são independentes: o prompt vai por copiar/colar.

Repositório: <https://github.com/luizabgk/gera-render-prompt>
Executável: `releases/GeraRender.exe`

---

## Novidades da versão 2.0

- **Prompt negativo é removido automaticamente** se for colado junto no GeraRender. O Mystic não tem campo negativo.
- Aviso ao gerar sem imagem de referência e quando há LoRA selecionado sem referência.
- **Qualidade máxima:** gera 2 versões, mede a nitidez e mantém a melhor. A alternativa também é salva.
- Resolução somente **2k ou 4k**; a opção 1k foi removida.
- **Força do LoRA ajustável (30–80).** O valor 100 era o padrão e dominava o prompt; 30–60 preserva melhor a cena.
- **Linhas de lote (opcional):** segundo campo de imagem para usar uma planta com divisas como `structure_reference` no Mystic. O estilo fica na imagem de referência.
- **F5** atualiza a interface e recarrega a lista de LoRAs.
- Cada geração salva um `.json` ao lado da imagem com prompt, motor, resolução, referência, estrutura, LoRA e parâmetros.
- Nitidez automática leve ao salvar o JPG.

---

## Como usar

1. Escolha a pasta de saída.
2. Se quiser guiar o acabamento, selecione **1. Imagem de referência (estilo)**.
3. Para masterplan, selecione também **1b. Linhas de lote (opcional)** com a planta que tem as divisas.
4. Cole o **prompt limpo** do GeraPrompt.
5. Escolha motor, proporção, estilo, acabamento e resolução.
6. Se for usar LoRA, deixe as imagens de referência vazias e ajuste a força para **30–60**.
7. Clique em **GERAR RENDER** ou pressione **F5** apenas para atualizar a interface/LoRAs.

### Regra importante: referência x LoRA

A API do Mystic **ignora o LoRA** quando existe `style_reference` ou `structure_reference`.

Escolha um dos caminhos:

| Objetivo | Configuração |
|---|---|
| Fidelidade à cena e ao acabamento | Imagem de referência de estilo + LoRA desligado |
| Preservar linhas de lote | Referência de estilo + planta com divisas em **Linhas de lote** + LoRA desligado |
| Estilo autoral do LoRA | Sem imagens de referência + LoRA em 30–60 |
| Edição fiel de uma base | Motor Seedream 5 Pro Edit + imagem de referência |

---

## Motores

### Mystic

Usado para cenas 3D, perspectivas e conceitos.

- Aceita `style_reference`, `structure_reference`, engine e resolução.
- `model: realism` é o padrão para arquitetura ampla.
- `engine: magnific_sharpy` é o recomendado para arquitetura e detalhes nítidos.
- LoRA entra em `styling.styles` pelo **nome**, com `strength`.
- LoRA é ignorado quando há referência de estilo ou estrutura.

### Seedream 5 Pro Edit

Usado para editar uma imagem-base preservando melhor a composição.

- Exige imagem de referência.
- Não usa o campo de linhas de lote do Mystic.
- Resolução: 1.5k ou 2k.
- Bom para planta humanizada, alteração de imagem e preservação do desenho.

---

## Instalação

### Opção A: executável

1. Baixe `releases/GeraRender.exe`.
2. Crie sua chave em <https://www.magnific.com/user/api-keys>.
3. Defina a variável de ambiente no Windows:

```powershell
setx MAGNIFIC_API_KEY "sua_chave_aqui"
```

4. Feche e abra o terminal/aplicativo para a variável ser lida.
5. Execute `GeraRender.exe`.

### Opção B: Python

Requisitos: Python 3.10+.

```powershell
pip install pillow numpy
setx MAGNIFIC_API_KEY "sua_chave_aqui"
python geraprompt_render.py
```

Para gerar o executável:

```powershell
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --windowed --icon GR.ico --name GeraRender --hidden-import numpy geraprompt_render.py
```

---

## Campos da interface

| Campo | Função |
|---|---|
| **1. Imagem de referência (estilo)** | Guia materiais, luz, vegetação e acabamento. Enviada como `style_reference`. |
| **1b. Linhas de lote (opcional)** | Planta com divisas. Enviada como `structure_reference` para preservar o traçado. |
| **2. Prompt** | Cole o prompt limpo do GeraPrompt. |
| **Motor** | Mystic ou Seedream. |
| **Proporção** | 16:9, 1:1, 4:3, 3:4, 9:16 ou 3:2. |
| **Estilo** | Modelo nativo do Mystic. |
| **Acabamento** | Engine do Mystic. |
| **Resolução** | 2k ou 4k no Mystic; 1.5k ou 2k no Seedream. |
| **Qualidade máxima** | Gera 2 versões e escolhe a mais nítida. Usa 2 gerações. |
| **LoRA** | Estilo treinado na conta Magnific. |
| **Força do LoRA** | 30–80. Recomendado 30–60. |
| **Pasta de saída** | Onde o JPG e o JSON serão salvos. |

---

## Segurança

- A chave **nunca** deve ser colocada no código ou no GitHub.
- O app lê a chave da variável de ambiente `MAGNIFIC_API_KEY`.
- O repositório não contém a chave.
- A API do Magnific é paga; cada geração consome créditos.
- As imagens de referência são ativos locais do escritório e não são versionadas no repositório público.

---

## Solução de problemas

| Problema | Solução |
|---|---|
| `400` ou `401` | Confira a chave e se a variável foi definida em um terminal novo. |
| LoRA não muda o resultado | Verifique se há referência de estilo/estrutura; nesse caso a API ignora o LoRA. |
| LoRA deixa a imagem mole | Reduza a força para 30–50. |
| Imagem tremida | Confirme 2k/4k, prompt limpo, referência nítida e força do LoRA entre 30–60. |
| Linhas de lote desapareceram | Use a planta com divisas em **1b. Linhas de lote**. |
| Seedream não aceita linhas de lote | Use Mystic para esse recurso. |
| Erro de água/lago | Mantenha a trava de água ativada e use uma referência com o contorno correto. |

---

## Estrutura do repositório

```text
geraprompt-render/
  geraprompt_render.py   GUI
  geraprompt_agente.py   chamadas à API
  README.md
  G.ico / GR.ico
  releases/GeraRender.exe
```

## Licença

MIT. Veja [LICENSE](LICENSE).
