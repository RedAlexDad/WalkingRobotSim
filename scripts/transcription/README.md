# scripts_custom

Кастомные скрипты для транскрибации длинного видео/аудио через whisper.cpp
с GPU-акселерацией (CUDA).

## Зачем

Whisper large-v3 на длинных аудио склонен к галлюцинациям — зацикливанию
(повторение одной фразы десятки раз), особенно на тихих участках. Стандартный
однопроходный запуск на 80-минутной лекции давал ~26 повторов одной фразы.

Решение: рвём аудио на независимые чанки по 120 секунд (с перекрытием 5с),
транскрибируем каждый отдельно без контекста и склеиваем результат. При таком
подходе контекст whisper сбрасывается на каждом чанке и галлюцинации исчезают.

## Сборка whisper.cpp с CUDA

```bash
cmake -S . -B build_cuda -DGGML_CUDA=ON \
      -DCMAKE_CUDA_COMPILER=/usr/local/cuda-13.2/bin/nvcc -DGGML_CCACHE=OFF
cmake --build build_cuda --target whisper-cli --parallel 12
```

Примечание: CUDA 13.1 несовместима с GCC 15/16 (ошибка `rsqrt` в headers glibc).
Используйте CUDA 13.2 или clang++ как host-компилятор.

## Использование

```bash
# 1. Транскрибация чанками (по умолчанию: русский, large-v3, чанк 120с)
./chunk_transcribe.sh input.mp4 /tmp/whisper/chunks

# 2. Склейка в единые .srt и .txt
./merge.py /tmp/whisper/chunks /tmp/whisper/full
```

### chunk_transcribe.sh

```
./chunk_transcribe.sh <media> [out_dir] [chunk_sec] [overlap_sec] [lang] [model]
```

Окружение: `WHISPER_CLI`, `WHISPER_MODEL` — переопределение путей
к бинарю и модели.

### merge.py

```
./merge.py <chunks_dir> [out_prefix] [chunk_sec] [overlap_sec]
```

## Выход

- `*.srt` — субтитры (для плееров, YouTube)
- `*.txt` — сплошной текст транскрипта