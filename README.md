# GeraPrompt Render

Gera **cenas 3D** (perspectivas) a partir de uma imagem de referência + um prompt, usando a API do [Magnific](https://www.magnific.com).

Faz parte do ecossistema **GeraPrompt**:
- **GeraPrompt** (HTML) → plantas (top-down fiel)
- **GeraPrompt Render** (este) → cenas 3D (conceito/perspectiva)

---

## O que ele faz

1. Você anexa uma **imagem de referência** (foto, cena, projeto)
2. Cola um **prompt** (do GeraPrompt ou digitado)
3. Escolhe a **proporção** (16:9, 1:1, 4:3, 3:4, 9:16) e o **estilo** (super_real, realism, fluid, zen, flexible)
4. Clica em **GERAR RENDER**
5. A imagem é gerada pela API do Magnific e salva na pasta escolhida

---

## Instalação (rodando o código)

1. Instale o **Python 3.10+** (https://python.org)
2. Instale as dependências:
   `
   pip install pillow
   `
3. Crie a sua chave de API em https://www.magnific.com/user/api-keys
4. Defina a variável de ambiente (Windows):
   `
   setx MAGNIFIC_API_KEY "sua_chave_aqui"
   `
   (ou crie um .env com MAGNIFIC_API_KEY=sua_chave)
5. Rode:
   `
   python geraprompt_render.py
   `

### Ou use o .exe (sem Python)
Baixe o GeraRender.exe na aba **Releases** e execute. A chave é a mesma (variável de ambiente).

---

## Uso

| Campo | O que é |
|---|---|
| **Imagem de referência** | a foto/cena que ensina o estilo |
| **Prompt** | o texto (cole do GeraPrompt ou escreva) |
| **Proporção** | a saída (16:9, 1:1, 4:3, 3:4, 9:16) |
| **Estilo** | o modelo do Mystic (super_real = mais fotorrealista) |
| **Pasta de saída** | onde o JPG será salvo |

**Dica**: prompt curto (5–10 palavras) + referência boa = melhor resultado. O prompt do GeraPrompt já vem otimizado.

---

## Modelos (estilo) aceitos pela API

| Modelo | Quando usar |
|---|---|
| super_real | fotorrealismo máximo (o padrão) |
| ealism | realista |
| luid | mais fluido/artístico |
| zen | minimalista |
| lexible | mais criativo |

---

## Estrutura

`
AGENTE-MN/
  geraprompt_render.py   ← a GUI (este app)
  geraprompt_agente.py   ← o core (chamadas à API)
  README.md
  G.ico / GR.ico
`

---

## Segurança

**NUNCA** coloque a sua chave de API no código. Use a variável de ambiente MAGNIFIC_API_KEY.
O app lê a chave do ambiente — se você publicar o código, ninguém vê a sua chave.

---

## Licença

Uso pessoal e profissional. A API do Magnific é paga (créditos por geração).
