# Arquitetura

## Princípio

`core/` não importa Qt. Nenhuma linha. Isso permite testar o pipeline inteiro
sem interface e sem servidor gráfico, e é verificado por um teste que importa
o core num subprocesso limpo e falha se algum módulo do PySide6 aparecer
carregado.

```
core/            pipeline, sem Qt
  formats.py     deteção por magic bytes
  engines.py     resolução de binários por SO + PATH
  runner.py      execução de processos (regex, 10 FPS, ok_codes, WinError 740)
  stages/        uma etapa por motor (Strategy + Registry)
  planner.py     rota mais curta entre formatos (BFS incremental)
  workspace.py   área de trabalho e política de colisões
  job.py         fila, transação dos originais, resultado
  events.py      eventos tipados com chave i18n
services/        paths, config, logging, som, updater
ui/              tema (tokens -> QPalette + QSS), widgets, telas
```

## Como uma etapa é adicionada

Criar um ficheiro em `core/stages/` com a classe decorada com `@register`:

```python
@register
class MinhaEtapa(Stage):
    id, engine = "meu", "meu-binario"
    consumes, produces = frozenset({Fmt.ALGO}), Fmt.OUTRO
    ok_codes = frozenset({0})          # códigos tolerados
    progress_re = re.compile(...)      # pré-compilado no módulo

    def output_for(self, artifact, ctx): return ctx.temp_path(".ext")
    def build_command(self, artifact, output, ctx): return [...]
```

E declarar o motor em `core/engines.py`. Mais nada: o planeador liga a etapa
ao grafo sozinho e só a usa se o binário existir.

### Etapas sem binário

Quando não há motor externo aceitável — é o caso dos contentores do Xbox 360,
em que as ferramentas são gráficas, só para Windows, ou não são
distribuíveis — a etapa herda de `NativeStage` e implementa `extract()` em vez
de `build_command()`:

```python
@register
class MinhaEtapa(NativeStage):
    id = "meu"                         # sem `engine`: não há o que resolver
    consumes, produces = frozenset({Fmt.ALGO}), Fmt.OUTRO

    def output_for(self, artifact, ctx): return ctx.temp_path(".ext")
    def extract(self, artifact, output, ctx, progress, should_cancel): ...
```

`progress(ratio, label)` chega já limitado a 10 FPS e levanta `Cancelled`
sozinho; `should_cancel()` cobre os intervalos sem progresso a reportar. A
pausa também funciona — bloqueia o worker no mesmo `CancelToken` em vez de
mandar SIGSTOP. Tudo o resto (planeador, pesos do progresso, transação dos
originais) é igual, e `available()` devolve sempre `True`.

Uma etapa pode também propor um nome melhor para o resultado com
`ctx.suggest_name(...)`. Só é usado quando o ficheiro se chama, por exemplo,
`8A1B2C3D` — se o utilizador já lhe deu um nome legível, esse é que manda.

## Como o planeador decide

1. `sniff()` identifica o item pelo conteúdo.
2. O modo dá o formato alvo (modos fixos) ou o perfil dá-o (modo automático).
3. BFS sobre `consumes -> produces` das etapas **disponíveis** devolve a rota.
4. Executa-se a primeira etapa e volta-se ao passo 1 com o resultado.

Voltar ao passo 1 é o essencial: só depois de abrir um `.7z` é que se sabe o
que estava lá dentro. É por isso que `zip -> gc_iso -> rvz` funciona sem uma
linha de código dedicada a essa combinação.

Se não houver rota, o item é ignorado com o nome do motor em falta -- não
falha silenciosamente nem inventa um destino.

## Proteções que vivem no ProcessRunner

| Proteção | Onde |
|---|---|
| Regex de progresso pré-compilado | `runner.PROGRESS_PATTERN` e `Stage.progress_re` |
| Limitador de atualização a 10 FPS | `ProcessRunner.refresh_interval` |
| Código 1 do 7-Zip tolerado | `ArchiveExtract.ok_codes = {0, 1}` |
| WinError 740 (UAC) | `ProcessRunner.run`, `ElevationRequired` |
| Motor apagado pelo antivírus | `EngineResolver.require` -> `EngineMissing` |
| Pasta portátil no Windows | `services/paths.py` |

A leitura do stdout corre numa thread dedicada. No código antigo um
`stdout.read(1)` bloqueante fazia com que um motor silencioso ignorasse o
cancelamento.

## Transação dos originais

Todas as etapas escrevem em `<destino>/.zarmanager-work/<job>/<item>/`.
Ficar dentro do destino é deliberado: o `os.replace` final é instantâneo por
ser no mesmo sistema de ficheiros, ao contrário de `/tmp`, que muitas vezes é
tmpfs — extrair 7 GB para RAM não acaba bem.

O original só é apagado depois de o artefacto final existir no destino.

## Roadmap dos motores

| Motor | Estado | Nota |
|---|---|---|
| `dolphin-tool` (RVZ) | etapa pronta | confirmar se a versão imprime percentagem; se não, a barra fica indeterminada |
| `chdman` (CHD) | etapa pronta | `createcd` para CD/cue, `createdvd` para DVD — escolhido pelo formato detectado |
| STFS (XBLA/DLC) | **nativo, pronto** | sem binário: lido em Python (`core/xbox/stfs.py`). Sempre disponível, nada que o antivírus possa apagar |
| GOD / SVOD | **nativo, por validar** | reconstrói o XDVDFS e entrega-o ao `extract-xiso`. A geometria é escolhida por tentativa e validada contra a assinatura do disco; falta confirmá-la com um pacote de retalho |
| PKG (PS3/PS4) | experimental | o shadPS4 lê `.zar` desde a 0.17.0, por isso a cadeia PKG -> `.zar` tem destino. Falta o motor: um `.pkg` de retalho é cifrado e o PkgTool só trata fPKG/debug |

`chdman` e `dolphin-tool` são GPL-2.0-or-later. Distribuí-los em `bin/` como
programas separados é aceitável, mas obriga a incluir o texto da licença e a
apontar para o código-fonte.
