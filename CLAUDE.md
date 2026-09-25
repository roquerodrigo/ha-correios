# CLAUDE.md

Orientações para agentes do Claude Code (claude.ai/code) que trabalham neste repositório.

## Sempre leia o `CODE_STYLE.md` primeiro

Antes de criar, renomear ou reestruturar qualquer arquivo/classe/função, **leia o [`CODE_STYLE.md`](./CODE_STYLE.md)**. Ele é a única fonte da verdade para as convenções: idioma, organização de arquivos, nomenclatura, tipagem, propriedades vs. `__init__`, imports, docstrings, comentários, padrão do coordinator, layout de repairs/diagnostics, traduções e fluxo de lint.

Para os assuntos voltados ao usuário (o que a integração faz, instalação, opções, entidades), consulte o [`README.md`](./README.md).

Este arquivo evita deliberadamente repetir essas regras — ele só acrescenta:

1. O fluxo de verificação que os agentes devem executar após cada alteração.
2. O raciocínio arquitetural que não é evidente apenas pelo `CODE_STYLE.md`.

## Idioma do repositório

O `hacs.json` declara `"country": ["BR"]`, então o idioma do repositório é o **português do Brasil**: documentação, docstrings, comentários, mensagens de commit, títulos e descrições de PR, changelog, templates de issue/PR e toda comunicação pública. O **código continua em inglês** (identificadores, nomes de arquivo e de branch, chaves, mensagens de log, tipo e escopo do Conventional Commit), e os termos nativos do domínio nunca são traduzidos. A regra completa está na seção "Idioma" do `CODE_STYLE.md`.

## Fluxo de verificação

**Após cada alteração de código, sempre execute o lint e depois os testes, nessa ordem, antes de declarar a tarefa concluída. Execute `scripts/lint` (um wrapper fino que apenas encadeia os comandos abaixo) ou execute-os diretamente:**

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy custom_components/correios
uv run pytest
node --check custom_components/correios/www/correios-card.js
```

- O lint executa `ruff format`, `ruff check` e `mypy` — todos configurados no `pyproject.toml`. Corrija qualquer falha e execute novamente antes de prosseguir.
- O `pytest` impõe um **gate de cobertura de 90 %** (`--cov-fail-under` no `pyproject.toml`).

Os dois gates espelham o CI (`.github/workflows/ci.yml`). Só os dispense quando a alteração literalmente não puder afetar lint nem testes (por exemplo, edições apenas no README).

## Atualização da versão do Home Assistant

A versão do Home Assistant é fixada em dois lugares e **precisa ser atualizada em conjunto**; caso contrário, CI, HACS e o harness de testes se desalinham:

1. `pyproject.toml`, `[dependency-groups] dev` — `homeassistant==<X.Y.Z>` (runtime/lint do CI + mypy) **e** `pytest-homeassistant-custom-component==<release correspondente>` (o harness de testes traz o seu próprio `homeassistant` fixado; os dois pins precisam vir do mesmo release do HA, senão lint e testes resolvem cores diferentes).
2. `hacs.json` — `"homeassistant": "<X.Y.Z>"` (versão mínima do HA core exigida pelo HACS).

Confira o pareamento no PyPI antes de commitar: o `requires_dist` do `pytest-homeassistant-custom-component` precisa listar o mesmo `homeassistant==<X.Y.Z>` fixado no `pyproject.toml`.

## Convenções que não são evidentes pelo código

A integração segue o padrão `DataUpdateCoordinator` do HA. Algumas escolhas não ficam evidentes pela leitura de um único arquivo:

- O estado vive em `entry.runtime_data` (descartado automaticamente no unload), **nunca** em `hass.data`.
- O `data/__init__.py` guarda os aliases `type` (`CorreiosConfigEntry`, `CorreiosPackages`, `Json*`) **e** reexporta todos os símbolos dos módulos irmãos, de modo que o código consumidor importa tudo de `.data`.
- **Não existe API oficial.** O `api.py` opera o site público de rastreamento: o formulário de login único em `cas.correios.com.br` (um token `execution` oculto mais usuário/senha) e, em seguida, os endpoints JSON que o próprio JavaScript do site chama (`app/controle.php` para o status da sessão, `app/rastrocpfcnpj.php` para os pacotes). A autenticação é baseada em cookies, então o cliente **precisa** receber uma sessão criada com `async_create_clientsession` — a sessão compartilhada do Home Assistant misturaria os cookie jars.
- A listagem de pacotes responde a uma requisição anônima com uma lista vazia (`[]`) em vez de um erro. Por isso o `async_get_packages` confere o status da sessão antes de confiar em uma resposta vazia e faz login novamente quando a sessão expirou; apenas um login rejeitado (HTTP 401 do formulário de login) vira `CorreiosApiClientAuthenticationError` → `ConfigEntryAuthFailed` → reauth.
- O `package_parser.py` é o único lugar que conhece os nomes de campo do site (em português, com caixa inconsistente). Tudo acima dele trabalha com as dataclasses `CorreiosPackage` / `CorreiosPackageEvent`.
- O payload do coordinator é `dict[tracking_code, CorreiosPackage]`, já filtrado: pacotes em trânsito mais os entregues dentro da opção `delivered_retention_days`. O `coordinator.latest_changes` guarda o que o `package_changes.py` detectou em relação ao payload anterior; a entidade de evento anuncia essas mudanças e nada é anunciado na primeira atualização.
- O `sensor.py` adiciona um `CorreiosPackageSensor` para cada código de rastreamento novo e remove do entity registry as entradas dos pacotes que saíram do payload (o coordinator só deixa um pacote sair depois de ele estar ausente da resposta do site por mais que o `MISSING_PACKAGE_GRACE_PERIOD`, porque o site às vezes devolve a listagem vazia para uma sessão válida) — a cada atualização do coordinator e uma vez no setup, o que também limpa sobras de quando o Home Assistant esteve fora do ar.
- As classes de entidade ficam uma por arquivo em `sensors/`; o `sensor.py` apenas conecta a plataforma.
- O card complementar fica em `www/correios-card.js` (web component vanilla sem build, com as traduções embutidas) e é servido em `/correios`. O `card_registration.py` o registra como **recurso de dashboard do Lovelace** com `?v=<versão da integração>-<fingerprint do conteúdo do card>` como cache-buster, de modo que um card editado invalida os caches do navegador mesmo sem mudança de versão — e não por `add_extra_js_url`, que disputa corrida com o frontend na inicialização; essa rota permanece apenas como fallback para recursos em modo YAML. O card descobre os sensores de pacote por `hass.entities` (`platform == "correios"`, `translation_key == "package"`), portanto depende de esses dois valores permanecerem estáveis.
- O diagnostics nunca inclui códigos de rastreamento nem detalhes em texto livre: um código de rastreamento identifica a encomenda de uma pessoa.
