# Guia de estilo de código

Convenções de estilo do projeto `ha-correios`. Antes de commitar,
execute `uv run ruff format --check .`, `uv run ruff check .` e
`uv run mypy custom_components/correios` — todos precisam terminar sem erros.
Em seguida vem o `uv run pytest` (com o gate de cobertura de 90 %).

**Sempre leia este arquivo antes de adicionar ou reestruturar código.**

## Idioma

O `hacs.json` declara `"country": ["BR"]`: a integração só faz sentido no
Brasil, e por isso o idioma do repositório é o **português do Brasil**.

- **Tudo que é prosa lida por pessoas fica em pt-BR:**
  - Documentação: `README.md`, `CONTRIBUTING.md`, este arquivo, `CLAUDE.md`,
    qualquer outro Markdown, docstrings e comentários de código.
  - Histórico do Git: assunto e corpo dos commits, títulos e descrições de PR.
  - Releases: notas de release e `CHANGELOG.md`, inclusive os títulos de seção
    (`changelog-sections` no `release-please-config.json`).
  - Comunicação pública: issues, comentários em issues e PRs, reviews,
    discussions, os templates de issue e o template de PR em `.github/`.
  - Metadados do repositório: a descrição no GitHub e o `description` do
    `pyproject.toml`.
- **O código continua em inglês**: nomes de arquivo, de classe, de função e de
  variável, nomes de branch, chaves de dicionário, strings identificadoras e
  mensagens de log. Tudo que uma ferramenta interpreta também é código: o tipo e
  o escopo do Conventional Commit (`feat(sensor): adiciona o prazo de entrega`),
  o rodapé `BREAKING CHANGE:`, ids de workflow e de job, labels.
- **Termos nativos do domínio mantêm o idioma original, no código e na prosa.**
  Eles são a linguagem ubíqua compartilhada com os usuários e com o site dos
  Correios; traduzi-los só obriga todo mundo a fazer o caminho de volta:
  `cpf`, `cnpj`, `cep`, `idCorreios`, nunca uma versão em inglês. O que envolve
  o termo segue em inglês. Identificadores perdem os acentos (`previsao`); a
  prosa e as strings traduzidas os mantêm (`previsão`).
- O idioma da conversa com o usuário nunca decide o que é gravado em disco.
- As strings voltadas ao usuário ficam apenas em
  `custom_components/correios/translations/{en,pt-BR}.json` — nunca fixas no
  Python. O `en.json` continua obrigatório ao lado do `pt-BR.json`.

## Organização de arquivos

- **Uma classe de nível superior por arquivo — inclusive TypedDicts e
  dataclasses.** Várias classes semanticamente relacionadas (famílias de
  exceções, entidades de sensor de uma plataforma, os payloads tipados e os
  dados de runtime) são agrupadas em um diretório de pacote, com uma classe por
  submódulo e um `__init__.py` reexportando os símbolos públicos.
  - Exemplo: `exceptions/` contém `api_client_error.py`,
    `api_client_communication_error.py`, `api_client_authentication_error.py`,
    além do `__init__.py`.
  - Exemplo: `data/` contém `package.py`, `package_event.py`,
    `config_data.py`, `options_data.py`, `diagnostics_entry.py`,
    `diagnostics_payload.py`, `runtime.py` e outros, além de um
    `__init__.py`. Cada TypedDict e cada dataclass tem o seu próprio arquivo —
    um `data.py` plano com várias classes é dívida de migração, não um layout
    válido.
  - **Flexibilizações**: um TypedDict ou alias `type` consumido por um único
    módulo pode viver nesse módulo consumidor em vez de ter arquivo próprio, e
    dataclasses folha que descrevem fragmentos do mesmo payload podem dividir um
    módulo. O layout de pacote com uma classe por submódulo continua sendo o
    padrão a partir do momento em que uma estrutura é compartilhada entre
    módulos.
- **Os aliases `type` são a exceção: eles vivem em `data/__init__.py`**, junto
  das reexportações (`JsonPrimitive`, `JsonValue`, `JsonObject`,
  `CorreiosConfigEntry`), e não em arquivos próprios.
- **Funções auxiliares** podem viver no mesmo arquivo da única classe que as usa
  (por exemplo, `_verify_response_or_raise` em `api.py`).
- **O `__init__.py` do pacote da integração** conecta `async_setup_entry`,
  `async_unload_entry`, `async_reload_entry` e nada mais.

## Entidades: uma classe por entidade

- **Uma classe por entidade.** Toda entidade tem a sua própria classe dedicada —
  nunca compartilhe uma classe genérica parametrizada por uma subclasse de
  `EntityDescription` com campos chamáveis como `value_fn` ou `action_fn`.
  Codifique o comportamento da entidade diretamente na classe, via `@property` e
  constantes `_attr_*` de nível de classe (ou uma instância simples de
  `EntityDescription` atribuída no nível da classe).
  - Não escreva uma subclasse `<DOMAIN><Platform>Description` com um campo
    `value_fn` / `action_fn`.
  - Escreva `<DOMAIN><Name><Platform>` (por exemplo, `CorreiosStatusSensor`,
    `CorreiosCancelButton`, `CorreiosDoorBinarySensor`).
- O motivo: cada entidade é um contrato distinto; misturá-las em uma classe
  genérica esconde o contrato atrás de indireção e desestimula o refinamento por
  entidade (ícones, atributos de estado, lógica própria).
- **Os ícones das entidades ficam no `icons.json`**
  (`entity.<platform>.<translation_key>.default`), indexados pelo
  `translation_key` da entidade — e não em `_attr_icon`. O arquivo de ícones
  aceita variantes por estado e por faixa e mantém a apresentação fora do
  Python.

## Nomenclatura

- Classes públicas têm o prefixo `Correios`.
- Entidades concretas de plataforma terminam com o tipo da entidade:
  `CorreiosSensor`, `CorreiosBinarySensor`,
  `CorreiosSwitch`.
- Classes de exceção terminam com `Error`: `CorreiosApiClientError`,
  `…CommunicationError`, `…AuthenticationError`.
- Atributos / funções privados têm o prefixo `_`.

## Tipagem

**Tipagem estrita. Sem genéricos, sem `Any`.** O mypy (`uv run mypy custom_components/correios`) impõe isso.

Proibidos: `typing.Any`, `object` como tipo de valor, `dict` / `list` / `tuple` /
`set` sem parâmetros, `dict[str, Any]`, `Mapping[str, Any]`.

Obrigatórios:

- `TypedDict` para estruturas conhecidas de dict / JSON (veja o pacote `data/`
  para os exemplos canônicos: `CorreiosConfigData`,
  `CorreiosOptionsData`, `CorreiosDiagnosticsPayload`,
  um por arquivo).
- `@dataclass` para registros estruturados (`CorreiosData` em
  `data/runtime.py`).
- Aliases `type` nomeados para estruturas recursivas / compartilhadas —
  `JsonPrimitive`, `JsonValue`, `JsonObject` em `data/__init__.py`.
- `frozenset[str]` / `tuple[str, ...]` para coleções fixas de strings.
- `cast("TypedDictName", value)` nas fronteiras com o framework do HA que nos
  entregam um tipo permissivo (por exemplo, `entry.data` é
  `MappingProxyType[str, Any]`).

Ao estreitar a assinatura de um callback fornecido pelo HA (por exemplo,
`async_step_user`), o mypy reporta `[override]` (violação de Liskov). Adicione
`# type: ignore[override]` com um comentário de uma linha explicando o
estreitamento deliberado — veja o `config_flow.py` para o exemplo canônico.

## Propriedades e `__init__`

- **Sempre prefira `@property`** a atribuir valores `_attr_*` no `__init__`.
  As propriedades são calculadas sob demanda a partir de campos guardados na
  classe pai (por exemplo, `self.coordinator`, `self.entity_description`).
- Quando o corpo do `__init__` só chamaria `super().__init__(...)`, omita o
  `__init__` por completo e deixe o Python herdar o da classe pai.
- Constantes de nível de classe como `_attr_attribution = ATTRIBUTION` e
  `_attr_has_entity_name = True` são aceitáveis — elas não dependem do estado da
  instância.

## Imports

- Sempre comece todo módulo com `from __future__ import annotations`, para que
  as anotações de tipo virem strings avaliadas sob demanda e o custo em runtime
  dos imports sob `if TYPE_CHECKING` seja zero.
- Imports relativos dentro do mesmo pacote (`from .module import …`) são o
  padrão.
- Mova os imports usados apenas para tipagem para um bloco `TYPE_CHECKING`
  (Ruff `TC001`/`TC003`):

  ```python
  from __future__ import annotations
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      from collections.abc import Mapping
      from .data import CorreiosConfigData
  ```

- Comentários `noqa` são reservados a restrições inevitáveis do framework (por
  exemplo, `# noqa: ARG001` para parâmetros de callback do HA que precisam
  existir mas ficam sem uso). Documente o motivo na própria linha quando não for
  óbvio. Nunca silencie uma regra para "agradar o ruff" — corrija o código.

## Docstrings

- Toda classe, função e método públicos (inclusive `@property`) e todo
  `__init__` têm docstring. O Ruff impõe isso via `D102`/`D107`.
- As docstrings são escritas em **português do Brasil**, no modo descritivo
  ("Retorna o …", "Representa um …").
- Uma única frase costuma bastar. Descreva o *contrato* ou o *porquê*, não a
  implementação óbvia.
- Docstring de módulo no topo de todo arquivo `.py`.
- Evite repetir o tipo — a assinatura já faz isso.

## Comentários

- O padrão é **não comentar**. Adicione um comentário apenas quando o *porquê*
  não for óbvio pelo código: uma restrição oculta, um contorno, uma invariante
  sutil ou uma sobreposição deliberada do sistema de tipos.
- Nunca descreva *o que* o código faz — identificadores bem nomeados cuidam
  disso.
- **Sem divisores de seção** como `# --- API payloads ---` para agrupar
  declarações relacionadas. Se um arquivo tem tantas seções que você sente falta
  de separadores visuais, divida-o em vários arquivos.

## Logging

- Cada módulo usa o `LOGGER` de nível de pacote definido em `const.py`
  (`LOGGER: Logger = getLogger(__package__)`); nunca chame
  `logging.getLogger(...)` de forma avulsa.
- As mensagens de log são código: ficam em **inglês**.
- Use **formatação `%` tardia**, nunca f-strings — elas forçam a interpolação da
  string mesmo quando o nível está filtrado:

  ```python
  LOGGER.warning("Refresh failed: %s", exception)   # ✓
  LOGGER.warning(f"Refresh failed: {exception}")    # ✗
  ```

- Níveis:
  - `debug` — resumos de consultas bem-sucedidas, diagnósticos de cada ciclo.
  - `info` — eventos únicos do ciclo de vida (setup concluído, fluxo de reauth
    iniciado).
  - `warning` — falhas recuperáveis (erro transitório da API, uso de fallback).
  - `error` / `exception` — falhas irrecuperáveis no ciclo atual; use
    `exception` com exceções capturadas dentro de blocos `except` para obter o
    traceback completo.
- Nunca registre segredos em log (`token`, `password`, `key`, cabeçalhos
  completos). O mapeamento `Coordinator → UpdateFailed` deve descartar a forma
  textual da exceção original quando ela puder expô-los.

## Mensagens de erro

- Formato: `"Failed to <verb> <object>: <cause>"`, em que `<cause>` é a exceção
  ou um motivo curto. Mantenha-as curtas e fáceis de localizar com grep.
- Valide as entradas antes da chamada de rede, para que os erros voltados ao
  usuário apontem para a entrada inválida, e não para um traceback posterior
  (`config_flow._validate` rejeita credenciais malformadas antes de contatar a
  API).
- As exceções próprias seguem a mesma hierarquia:
  `CorreiosApiClientError` (base) → `…CommunicationError` (timeout, conexão,
  DNS) e `…AuthenticationError` (401/403). Encapsule os erros crus do upstream
  na fronteira do cliente da API; tudo acima dele captura apenas a hierarquia
  própria.

## Coordinator e dados de runtime

- Todo o estado da API passa por `entry.runtime_data: CorreiosData`
  (`data/runtime.py`). Nunca guarde estado da integração em `hass.data` — o
  `runtime_data` é descartado automaticamente no unload; o padrão legado
  `hass.data[DOMAIN][entry_id]` não é.
- O coordinator é tipado como `DataUpdateCoordinator[CorreiosPackages]`
  (código de rastreamento → `CorreiosPackage`). O `_async_update_data` retorna o
  payload tipado.
- Use `await coordinator.async_config_entry_first_refresh()` durante o
  `async_setup_entry` (e não `async_refresh()`) — uma primeira atualização que
  falha lança `ConfigEntryNotReady`, e o HA tenta novamente com backoff de forma
  automática.
- Passe `always_update=False` ao coordinator quando o TypedDict do payload
  puder ser comparado de forma limpa com `__eq__`; o HA então pula os callbacks
  dos listeners e as escritas de estado quando os dados não mudaram.
- Use `self.async_contexts()` dentro do `_async_update_data` para limitar o
  trabalho de API às entidades atualmente inscritas — entidades desabilitadas
  não devem provocar chamadas de rede.
- Mapeamento de erros dentro do `_async_update_data`:
  - Erros de comunicação → `raise UpdateFailed("Failed to …: %s" % err)`. Passe
    `retry_after=<segundos>` quando o upstream sinalizar um backoff explícito
    (por exemplo, `Retry-After` de um HTTP 429).
  - Erros de autenticação → `raise ConfigEntryAuthFailed(...)` — o HA cancela as
    atualizações seguintes e inicia o fluxo `SOURCE_REAUTH`.
  - Nunca deixe strings cruas de exceções do upstream chegarem ao
    `UpdateFailed` quando puderem carregar tokens; converta-as em uma mensagem
    saneada no cliente da API.

## Config / options / repairs / diagnostics

- O `config_flow.py` contém os passos `user`, `reauth`, `reauth_confirm` e
  `reconfigure`, todos compartilhando um único helper `_validate` e um único
  construtor `_credentials_schema`.
- O `options_flow.py` contém a única classe `CorreiosOptionsFlow`. Novas chaves
  de opção entram no TypedDict `CorreiosOptionsData`, em
  `data/options_data.py`.
- Não existe `repairs.py`: a integração não registra issues. Adicione a
  plataforma junto com a primeira issue, com as strings em
  `issues.<issue_id>`.
- O `diagnostics.py` retorna `CorreiosDiagnosticsPayload`. As chaves sensíveis
  entram na constante `TO_REDACT: frozenset[str]`.

## Traduções

- Dois locales: `en.json` e `pt-BR.json`. O `tests/test_translations.py`
  parametriza todos os locales e falha se os conjuntos de chaves aninhadas
  divergirem.
- As strings de issue ficam em `issues.<issue_id>`; as de opções, em
  `options.step.init.data`; as de fluxo, em `config.step.<step_id>`; os nomes de
  entidade, em `entity.<platform>.<key>.name`.

## Requisitos de publicação no HACS

O [HACS](https://www.hacs.xyz/docs/publish/integration/) valida o formato do
repositório a cada push via `hacs/action@main` (e o próprio HA executa o
`hassfest`). Os dois gates precisam permanecer verdes:

- **Uma integração por repositório**, localizada em
  `custom_components/<domain>/`.
- O `manifest.json` precisa declarar `domain`, `name`, `version`,
  `documentation`, `issue_tracker` e `codeowners`. A chave `version` é
  **obrigatória em integrações custom** (omita-a apenas em integrações do core)
  e precisa ser interpretável como `AwesomeVersion` — CalVer ou SemVer.
- O `manifest.json` também declara `integration_type`. JSON não aceita
  comentários, então a escolha fica registrada aqui: `service`, porque uma
  config entry representa uma conta em um serviço de nuvem.
- O `hacs.json`, na raiz do repositório, fixa a versão mínima do HA core pela
  chave `homeassistant`. Este é o terceiro pin do HA (veja o `CLAUDE.md`).
- O `hacs.json` declara `"country": ["BR"]` (ISO 3166-1 alpha-2): os Correios
  só existem no Brasil. Quem define outro país nas opções do HACS deixa de ver o
  repositório na loja; quem não define país, ou define o Brasil, continua vendo.
  É essa chave que torna o português do Brasil o idioma do repositório (veja
  "Idioma").
- Os assets de marca ficam em `custom_components/<domain>/brand/` — `icon.png`,
  `logo.png` (+ variantes `@2x`), com a marca dos Correios.
- Um `README.md` na raiz do repositório é obrigatório; o HACS o exibe como a
  descrição da integração. O cabeçalho dele segue o layout abaixo.

O release-please cria a tag dos releases a cada merge na `main`; o HACS exibe
aos usuários os cinco releases mais recentes do GitHub, então mantenha o
changelog fácil de localizar com grep.

## Cabeçalho do README

Todo repositório abre o `README.md` com o mesmo cabeçalho, exatamente nesta
ordem: **título → badges → link do HACS → separador `---` → o restante do
documento.**

```markdown
# <Título>

[![CI](https://github.com/roquerodrigo/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/<repo>/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=<repo>&category=integration)

---
```

- `owner=` é sempre `roquerodrigo`; `repository=` é o nome do repositório.
- `category=integration` para uma integração; `category=plugin` para um
  repositório de card do Lovelace.
- O link do HACS é um parágrafo próprio, separado do bloco de badges por uma
  linha em branco. A linha de badges e o botão "Open your Home Assistant
  instance" são coisas diferentes e não podem ficar juntos.
- Preserve os badges que o repositório já tem e não invente novos; todos eles
  ficam **antes** do link do HACS.
- O `---` logo após o link do HACS é o separador do cabeçalho. Um README que já
  usa `---` mais abaixo os mantém como quebras de seção — não adicione um
  segundo separador ao cabeçalho.

**Um repositório privado não recebe o link do HACS.** O `my.home-assistant.io`
resolve o destino pela API pública do GitHub, então, em um repositório privado,
o botão cai em algo que o HACS não consegue instalar. É o mesmo motivo pelo qual
esses repositórios chamam o workflow de validação com `hacs: false`. Entregue o
título, os badges e o separador, e adicione o link quando — e somente quando — o
repositório se tornar público.

## Quality scale

- O `quality_scale.yaml` é **opcional** e este repositório não o inclui. Ele só
  é obrigatório quando o `manifest.json` declara um nível de `quality_scale` — e,
  nesse caso, toda afirmação nele precisa ser honesta (`done` apenas quando a
  regra está de fato implementada; caso contrário, use `todo`/`exempt`).
- O objetivo é aplicar as [regras Bronze/Silver/Gold](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
  pertinentes à integração; Platinum é uma aspiração, não um gate de review.

## Hooks de pre-commit

O `pre-commit` é uma dependência de desenvolvimento (`pyproject.toml`), e o
`.pre-commit-config.yaml` executa ruff format, ruff check e mypy como **hooks
locais via `uv run`**, de modo que todo commit usa exatamente as versões de
ferramenta fixadas em `pyproject.toml`/`uv.lock` — as mesmas que o CI resolve.
Nunca troque esses hooks por hooks espelhados (`ruff-pre-commit`,
`mirrors-mypy`): um hook espelhado carrega o seu próprio pin de versão, que se
desalinha silenciosamente do pin do projeto. Instale uma vez por clone:

```bash
pre-commit install
```

O hook executa, a cada commit, os mesmos gates de lint do CI. Só o dispense em
um `git commit --no-verify` de emergência e, logo em seguida, execute novamente
`scripts/lint` (ou os comandos diretos equivalentes).

## Conventional commits

Todos os commits seguem o [Conventional Commits](https://www.conventionalcommits.org/),
que o `release-please` interpreta para incrementar a versão e gerar o
`CHANGELOG.md`:

| Tipo | Significado | Incremento |
|---|---|---|
| `feat` | Nova funcionalidade | minor |
| `fix` | Correção de bug | patch |
| `perf` | Melhoria de desempenho | patch |
| `deps` | Atualização de dependência | patch |
| `docs` | Apenas documentação | nenhum |
| `refactor` | Refatoração sem mudança de comportamento | nenhum |
| `test` | Mudança apenas em testes | nenhum |
| `ci` | Mudança de CI / ferramentas | nenhum |
| `chore` | Qualquer outra coisa (raramente) | nenhum |

- Linha de assunto: modo imperativo, em minúsculas, sem ponto final, **em
  português do Brasil**. O tipo e o escopo ficam sempre em inglês.
- Use escopos quando for útil:
  `fix(sensor): mapeia valores de interface fora do enum para None`.
- Um rodapé `BREAKING CHANGE:` (ou `!` após o tipo) incrementa a versão major.

## Lint e verificação

- A configuração do Ruff fica no `pyproject.toml` (`[tool.ruff]`), com
  `select = ["ALL"]`.
- A configuração do mypy fica no `pyproject.toml` (`[tool.mypy]`). Execute os
  dois com `uv run ruff check .` e `uv run mypy custom_components/correios`.
- Após cada alteração, execute `uv run ruff format --check .`,
  `uv run ruff check .`, `uv run mypy custom_components/correios` e
  `uv run pytest`. Os dois gates espelham o CI. O `scripts/lint` é um wrapper
  fino que apenas encadeia esses quatro comandos — executá-lo ou executar os
  comandos diretamente dá no mesmo; o wrapper existe para que CI, documentação e
  hábitos locais compartilhem uma única fonte da verdade.
- Os testes ficam em `tests/`, espelhando o layout de produção. O gate de
  cobertura de 90 % (`pyproject.toml`, `[tool.pytest.ini_options]`) impede que
  código sem teste entre despercebido. Quando um teste exercita um estado
  impossível sob os novos tipos, atualize-o ou remova-o — nunca enfraqueça o
  tipo para satisfazer o teste.
