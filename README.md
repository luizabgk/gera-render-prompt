# GeraPrompt Render

Gera **cenas 3D** (perspectivas e conceitos) a partir de uma imagem de referência + um prompt, usando a API do [Magnific](https://www.magnific.com).

Faz parte do ecossistema **GeraPrompt**:
- **GeraPrompt** (HTML) -> plantas top-down fiéis, no Magnific web/Seedream.
- **GeraPrompt Render** (este app) -> cenas 3D e perspectivas no estilo MN, via API.

Os dois são independentes. O prompt vai por copiar/colar.

Repositório público e download: <https://github.com/luizabgk/gera-render-prompt/releases/tag/v1.5>

---

## Novidades da versão 1.5

- Novo motor **Seedream 5 Pro Edit**, agora o padrão para preservar melhor a imagem base.
- Checkbox **Não expandir lagos/água**: impede o modelo de transformar lago em mar.
- Fidelidade da estrutura ajustável em 90/95/98.
- **Imagem de referência agora é enviada como `structure_reference`** no Mystic, ou como `reference_images` no Seedream.
- **LoRA por nome:** o app carrega a lista da conta e mostra `nome (ID ...)`; não é mais preciso decorar números.
- A interface avisa que LoRA é ignorado quando a imagem é usada como estrutura.
- Novos controles de **Acabamento** (engine) e **Resolução**.
- Botão **Gerar prompt pela imagem** usando a API **Image to Prompt** do Magnific.
- A **imagem de referência** e o **LoRA** agora estão explicados na interface: são coisas diferentes.
- Campo de prompt começa **vazio**, para evitar gerar com prompt genérico.
- Correção dos acentos e da codificação UTF-8.
- Referências internas atualizadas para a pasta `_REFERENCIA_MN_3D`.

---

## O que ele faz

1. Você anexa uma **imagem de referência** (planta, foto, render ou cena). Ela é enviada como `structure_reference` para preservar o traçado.
2. Cola o **prompt gerado pelo GeraPrompt**.
3. Escolhe a **proporção** e o **estilo** do Mystic.
4. Opcionalmente informa um **ID de LoRA**.
5. Escolhe a pasta de saída e clica em **GERAR RENDER**.
6. O JPG é salvo na pasta escolhida.

O botão **Gerar prompt pela imagem** analisa a referência e preenche o campo de prompt automaticamente.

---

## Instalação

### Opção A: usar o executável

1. Baixe `GeraRender.exe` na aba **Releases** deste repositório.
2. Crie sua chave em https://www.magnific.com/user/api-keys.
3. Defina a variável de ambiente no Windows:

```powershell
setx MAGNIFIC_API_KEY "sua_chave_aqui"
```

4. Feche e abra o terminal/aplicativo para a variável ser lida.
5. Execute `GeraRender.exe`.

### Opção B: rodar pelo Python

Requisitos: Python 3.10+.

```powershell
pip install pillow
setx MAGNIFIC_API_KEY "sua_chave_aqui"
python geraprompt_render.py
```

---

## Uso

| Campo | O que é |
|---|---|
| **Imagem de referência** | imagem base; é enviada como `structure_reference` para preservar o traçado |
| **Prompt** | cole o texto do GeraPrompt ou gere pela imagem |
| **Gerar prompt pela imagem** | analisa a referência via API Image to Prompt e preenche o prompt |
| **Proporção** | 16:9, 1:1, 4:3, 3:4, 9:16 ou 3:2 |
| **Motor** | `Seedream 5 Pro Edit` (fiel à base) ou `Mystic` (cena 3D/conceito) |
| **Estilo** | modelo nativo do Mystic: `realism`, `super_real`, `flexible`, `fluid` ou `zen` |
| **Acabamento** | engine do Mystic: Sharpy, Sparkle, Illusio ou automático |
| **Resolução** | 1k, 2k ou 4k |
| **LoRA (opcional)** | escolha pelo nome na lista de estilos treinados da sua conta |
| **Pasta de saída** | onde o JPG será salvo |

**Dica:** use uma referência boa e um prompt curto. O prompt do GeraPrompt já vem otimizado para até ~2.000 caracteres.

---

## Seedream 5 Pro Edit x Mystic

- **Seedream 5 Pro Edit** — melhor para planta humanizada, alteração de imagem e preservação do desenho. É o motor padrão do app.
- **Mystic** — melhor para cenas 3D, perspectivas e conceito; aceita `structure_reference`, `style_reference` e engine.

O checkbox **Não expandir lagos/água** acrescenta uma trava explícita no prompt. No teste com uma prancha real, o Seedream manteve o contorno dos lagos e entregou uma planta humanizada com lotes vazios; o Mystic ainda exagerava a água.

---

## Estilos nativos do Magnific

Não existe um preset nativo chamado "arquitetura hiperrealista". O Mystic tem **modelos** e **engines** gerais. Para arquitetura, a recomendação é:

| Configuração | Quando usar |
|---|---|
| `model: realism` | **melhor padrão para arquitetura ampla** e plantas; cor mais natural e menos "cara de IA" |
| `model: super_real` | máximo realismo em cenas próximas/médias; pode criar artefatos em tomadas muito abertas |
| `model: flexible` | estudo conceitual, mais HDR/saturado |
| `model: fluid` | seguir o prompt com mais liberdade criativa |
| `model: zen` | resultado mais limpo e minimalista |
| `engine: magnific_sharpy` | fotos, arquitetura e detalhes nítidos |
| `engine: magnific_illusio` | ilustrações, natureza e aparência mais suave |
| `engine: magnific_sparkle` | meio-termo realista |
| `creative_detailing: 20–30` | evita o aspecto excessivamente "AI/HDR" |
| `structure_strength: 85–95` | segura o traçado da planta |

**Importante:** LoRA e `structure_reference`/`style_reference` não funcionam juntos. A API **ignora o LoRA silenciosamente** quando há referência de estrutura ou estilo. Para fidelidade de planta, use estrutura e deixe o LoRA desligado. Para estilo puro, desmarque a opção de estrutura e use o LoRA.

---

## Prompt automático pela imagem

O botão **Gerar prompt pela imagem** chama `POST /v1/ai/image-to-prompt` com a imagem de referência, acompanha a tarefa e coloca o texto descritivo no campo de prompt.

- **Vantagem:** parte da própria imagem, sem precisar escrever o prompt do zero.
- **Cuidado:** o texto gerado descreve o que a IA vê; ele não garante fidelidade geométrica. Revise antes de gerar.
- **Custo:** a análise usa créditos da API Magnific.
- **Edição:** depois de gerado, o prompt pode ser alterado normalmente.

Para melhores resultados, use o prompt automático como ponto de partida e acrescente as regras de preservação de geometria do GeraPrompt.

---

## LoRA

O campo LoRA é **opcional** e não é a imagem de referência:

- **Imagem de referência** é o botão **1** no topo: a imagem que será usada como base/oferecimento de cena.
- **LoRA** é um **estilo treinado** na conta Magnific. Ele muda a aparência, mas não substitui a imagem.

Na versão 1.3, o app consulta `GET /v1/ai/loras` e mostra uma lista com o nome de cada LoRA e o ID entre parênteses. Escolha pelo nome. O ID é enviado internamente como `lora_id`.

Se a lista não carregar, clique em **Atualizar**. Verifique a variável `MAGNIFIC_API_KEY` e a Internet.

LoRAs da conta da Luiza (referência interna):

| Nome | ID | Status |
|---|---:|---|
| `mn_style_3d` | 2456849 | concluído |
| `paisagismo_mn_3d_v2` | 2456900 | concluído |
| `paisagismo_plantas_v3` | 2457071 | concluído |
| `paisagismo_plantas_v4` | 2458156 | concluído (20 imagens de implantação) |

**Limitação importante:** o LoRA aplica **estilo**, mas o Mystic **não garante a geometria** da planta. Em teste real, o modelo alterou ruas, lotes e criou casas mesmo com prompt de preservação. Para fidelidade de implantação, use o **GeraPrompt + Seedream 5 Pro no Magnific web**.

---

## Modelos aceitos pela API

| Modelo | Quando usar |
|---|---|
| `super_real` | fotorrealismo máximo (padrão) |
| `realism` | realista |
| `fluid` | mais fluido/artístico |
| `zen` | minimalista |
| `flexible` | mais criativo |

---

## Segurança

- A chave **nunca** deve ser colocada no código ou no GitHub.
- O app lê a chave da variável de ambiente `MAGNIFIC_API_KEY`.
- O repositório não contém a chave.
- A API do Magnific é paga; cada geração consome créditos.

---

## Estrutura

```text
AGENTE-MN/
  geraprompt_render.py   GUI
  geraprompt_agente.py   chamadas à API
  README.md
  G.ico / GR.ico
  releases/GeraRender.exe
```

---

## Solução de problemas

| Problema | Solução |
|---|---|
| `400` ou `401` | Confira a chave e se a variável foi definida em um terminal novo. |
| Não encontra a chave | Rode `setx MAGNIFIC_API_KEY "..."` e abra o app de novo. |
| Geração falhou | Veja a mensagem no status; confira créditos e tamanho da imagem. |
| Imagem salva com formato errado | O app converte para JPG automaticamente. |
| LoRA não muda o resultado | Confirme o ID e use uma referência compatível; o LoRA pode ter força limitada. |

---

## Licença

MIT. Veja [LICENSE](LICENSE).
