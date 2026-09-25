# Correios

[![CI](https://github.com/roquerodrigo/ha-correios/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-correios/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-db61a2?logo=githubsponsors&logoColor=white&style=for-the-badge)](https://github.com/sponsors/roquerodrigo)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-correios&category=integration)

---

Integração para o [Home Assistant](https://www.home-assistant.io/) que rastreia
os pacotes dos [Correios](https://rastreamento.correios.com.br/app/index.php)
vinculados ao seu CPF ou CNPJ. Não há códigos de rastreamento para digitar: a
integração entra no site de rastreamento dos Correios com a sua conta e acompanha
todos os pacotes que o site lista para você — os endereçados a você e os que
você enviou.

## Requisitos

- Uma conta dos Correios (o mesmo usuário e a mesma senha usados no site e no
  aplicativo dos Correios). O usuário pode ser um CPF, um CNPJ ou um idCorreios.
- Home Assistant 2026.7.2 ou mais recente.

## Instalação

### HACS (recomendado)

1. Abra o repositório no HACS pelo botão acima, ou adicione
   `https://github.com/roquerodrigo/ha-correios` como repositório personalizado
   do tipo **Integração**.
2. Instale **Correios** e reinicie o Home Assistant.

### Manual

Copie `custom_components/correios/` para o diretório `custom_components/` da
configuração do seu Home Assistant e reinicie o Home Assistant.

## Configuração

Acesse **Configurações → Dispositivos e serviços → Adicionar integração →
Correios** e informe o seu usuário e a sua senha. Cada conta vira um dispositivo
de serviço, nomeado de acordo com a conta (um CPF é mascarado, por exemplo
`***.456.789-**`).

Opções (**Configurar** na entrada da integração):

| Opção | Padrão | Descrição |
| --- | --- | --- |
| Intervalo de consulta | 900 s | Frequência com que a lista de pacotes é atualizada (mínimo de 300 s). |
| Manter pacotes entregues por | 7 dias | Por quanto tempo um pacote entregue mantém o seu sensor. `0` o remove assim que é entregue. |

Se a senha mudar, o Home Assistant solicita a nova pelo fluxo de
reautenticação; as credenciais também podem ser editadas em **Reconfigurar**.

## Entidades

| Entidade | Descrição |
| --- | --- |
| `sensor.correios_<account>_packages_in_transit` | Quantidade de pacotes a caminho de você. O atributo `tracking_codes` os lista. |
| `sensor.correios_<account>_sent_packages_in_transit` | Quantidade de pacotes enviados por você que ainda não foram entregues. O atributo `tracking_codes` os lista. |
| `sensor.correios_<account>_next_delivery` | Previsão de entrega mais próxima entre os pacotes a caminho de você, como `timestamp` (início do dia previsto) para que a interface a formate conforme o idioma e as preferências do usuário. O atributo `tracking_code` indica qual é o pacote e `expected_delivery` traz a data em ISO. |
| `sensor.correios_<account>_package_<tracking code>` | Um por pacote rastreado. O estado é o status de rastreamento mais recente informado pelos Correios. |
| `event.correios_<account>_package_update` | Dispara `new_package`, `status_changed` ou `delivered` sempre que uma atualização detecta uma mudança. |

Os sensores de pacote são criados e removidos automaticamente: um pacote ganha
um sensor quando o site passa a listá-lo e o perde depois de estar entregue por
mais tempo do que a retenção configurada.

### Atributos do sensor de pacote

`tracking_code`, `direction` (`received` / `sent`), `delivered`, `delayed`,
`detail`, `location`, `category`, `expected_delivery`, `last_event_at` e
`events` — o histórico completo, do mais recente para o mais antigo, cada
entrada com `description`, `detail`, `occurred_at`, `location` e `destination`.
O atributo `events` não é gravado no recorder.

## Card de dashboard

A integração traz um card complementar e o registra como recurso de dashboard
durante o setup — não há nada para instalar. Adicione-o pelo seletor de cards
(**Correios**) ou em YAML:

```yaml
type: custom:correios-card
title: Pacotes
show_delivered: true
show_sent: true
show_history: true
max_events: 10
```

O card encontra sozinho os sensores de pacote, lista primeiro os pacotes em
trânsito e expande um pacote no seu histórico de rastreamento ao toque. Um
sensor de pacote renomeado no Home Assistant (por exemplo, "Teclado mecânico") é
exibido com esse nome, com o código de rastreamento logo abaixo.

| Opção | Padrão | Descrição |
| --- | --- | --- |
| `title` | `Correios` | Título do card. |
| `show_delivered` | `true` | Lista os pacotes entregues que ainda são rastreados. |
| `show_sent` | `true` | Lista os pacotes enviados pelo titular da conta. |
| `show_history` | `true` | Expande o histórico de rastreamento ao toque. Quando `false`, o toque abre o diálogo de mais informações. |
| `max_events` | `10` | Quantidade máxima de eventos exibidos no histórico. |

Em dashboards gerenciados em modo YAML, o recurso não pode ser registrado
automaticamente; nesse caso, o card é carregado como um módulo extra do
frontend.

### Exemplo de notificação

```yaml
automation:
  - alias: Correios - atualização de pacote
    triggers:
      - trigger: state
        entity_id: event.correios_456_789_package_update
        not_from: unavailable
    actions:
      - action: notify.notify
        data:
          title: "Correios {{ trigger.to_state.attributes.tracking_code }}"
          message: >-
            {{ trigger.to_state.attributes.status }}
            ({{ trigger.to_state.attributes.location }})
```

## Observações

- Status, detalhes e locais são exibidos exatamente como os Correios os
  informam.
- O site dos Correios tem indisponibilidades curtas e frequentes. Uma
  atualização que falha mantém os últimos dados conhecidos por até uma hora
  antes de as entidades ficarem indisponíveis. Da mesma forma, um pacote que
  some da listagem continua com os últimos dados conhecidos por até uma hora
  antes de perder o sensor, e a sua volta nesse intervalo não é anunciada como
  pacote novo.
- Este projeto não tem vínculo com os Correios. Ele depende do site público de
  rastreamento, que pode mudar sem aviso.

## Desenvolvimento

```bash
scripts/setup     # cria o .venv com uv e instala os grupos dev + lint
scripts/lint      # ruff format --check, ruff check, mypy, pytest, node --check no card
scripts/develop   # executa o Home Assistant com a integração carregada
```

As convenções para quem contribui estão em [`CODE_STYLE.md`](./CODE_STYLE.md) e
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Apoio

Esta integração é desenvolvida e mantida em tempo pessoal. Se ela for útil para você, considere [apoiar o trabalho](https://github.com/sponsors/roquerodrigo) — isso mantém o desenvolvimento, os testes e os releases em andamento.

## Licença

[MIT](LICENSE)
