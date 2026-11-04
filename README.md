# GeraPrompt Render

Gera **cenas 3D** (perspectivas e conceitos) a partir de uma imagem de referência + um prompt, usando a API do [Magnific](https://www.magnific.com).

Faz parte do ecossistema **GeraPrompt**:
- **GeraPrompt** (HTML) -> plantas top-down fiéis, no Magnific web/Seedream.
- **GeraPrompt Render** (este app) -> cenas 3D e perspectivas no estilo MN, via API.

Os dois são independentes. O prompt vai por copiar/colar.

Repositório público e download: <https://github.com/luizabgk/gera-render-prompt/releases/tag/v1.1>

---

## Novidades da versão 1.1

- Campo **LoRA (opcional)** para usar um estilo treinado na conta Magnific.
- Campo de prompt começa **vazio**, para evitar gerar com prompt genérico.
- Correção dos acentos e da codificação UTF-8.
- Referências internas atualizadas para a pasta `_REFERENCIA_MN_3D`.

---

## O que ele faz

1. Você anexa uma **imagem de referência** (planta, foto, render ou cena).
2. Cola o **prompt gerado pelo GeraPrompt**.
3. Escolhe a **proporção** e o **estilo** do Mystic.
4. Opcionalmente informa um **ID de LoRA**.
5. Escolhe a pasta de saída e clica em **GERAR RENDER**.
6. O JPG é salvo na pasta escolhida.

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
| **Imagem de referência** | imagem que orienta a composição/cena |
| **Prompt** | cole o texto gerado pelo GeraPrompt |
| **Proporção** | 16:9, 1:1, 4:3, 3:4, 9:16 ou 3:2 |
| **Estilo** | modelo do Mystic: `super_real`, `realism`, `fluid`, `zen` ou `flexible` |
| **LoRA (opcional)** | ID numérico de um LoRA de estilo da sua conta |
| **Pasta de saída** | onde o JPG será salvo |

**Dica:** use uma referência boa e um prompt curto. O prompt do GeraPrompt já vem otimizado para até ~2.000 caracteres.

---

## LoRA

O campo LoRA é opcional. Para usar, informe apenas o **ID numérico**, por exemplo:

```text
2457071
```

O app envia esse valor como `lora_id` no payload do Mystic.

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
