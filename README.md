# Public Opinion Analytics

一个可复用的离线舆情分析工具骨架，面向固定结构的评论 CSV 数据。

首版能力：

- 解析原始评论 CSV，并正确处理评论正文中的换行
- 标准化字段并输出结构化评论表
- 基于规则识别低信息文本、动员文本和模板复读文本
- 导出待送模型的 JSONL
- 合并模型返回标签
- 生成基础聚合报表

## 环境

- Python 3.11
- Poetry

初始化：

```bash
poetry install
```

复制配置模板并填写真实值：

```bash
Copy-Item .env.example .env
```

## 命令

### 1. 标准化原始评论

```bash
poetry run public-opinion normalize --input remark.csv --output data/normalized/comments.csv
```

### 2. 规则打标并导出待送模 JSONL

```bash
poetry run public-opinion prepare-model \
  --input data/normalized/comments.csv \
  --records-output data/processed/comments_rules.csv \
  --jsonl-output data/model_io/model_inputs.jsonl
```

### 3. 合并模型标签

模型返回文件当前约定为 JSONL，每行至少包含：

```json
{
  "comment_id": "303156161456",
  "template_group": "",
  "sentiment": "负面",
  "stance": "要求进一步处理",
  "topic_tags": ["处理方案"],
  "emotion_intensity": "高",
  "risk_tags": ["无明显风险"]
}
```

执行合并：

```bash
poetry run public-opinion merge-labels \
  --input data/processed/comments_rules.csv \
  --labels data/model_io/model_labels.jsonl \
  --output data/processed/comments_labeled.csv
```

### 3.1 批量标注流程

先把待送模 JSONL 切成批次：

```bash
poetry run public-opinion build-batches \
  --input data/model_io/model_inputs.jsonl \
  --output-dir data/model_io/batches \
  --batch-size 5000 \
  --run-id run_20260525_001
```

推荐把模型配置放在项目根目录 `.env` 中：

```bash
PUBLIC_OPINION_OPENAI_BASE_URL=https://your-openai-compatible-endpoint/v1
PUBLIC_OPINION_OPENAI_API_KEY=your-api-key
PUBLIC_OPINION_OPENAI_MODEL=your-model-name
PUBLIC_OPINION_OPENAI_TIMEOUT_SECONDS=60
```

对单个批次执行标注：

```bash
poetry run public-opinion run-batch-label \
  --input data/model_io/batches/run_20260525_001-batch-0001.jsonl \
  --output data/model_io/raw_results_0001.jsonl
```

如果不想使用 `.env` 中的 `PUBLIC_OPINION_OPENAI_BASE_URL` 或 `PUBLIC_OPINION_OPENAI_MODEL`，也可以显式传：

```bash
poetry run public-opinion run-batch-label \
  --input data/model_io/batches/run_20260525_001-batch-0001.jsonl \
  --output data/model_io/raw_results_0001.jsonl \
  --base-url https://your-openai-compatible-endpoint/v1 \
  --model your-model-name
```

校验模型返回并拆分合法结果与失败结果：

```bash
poetry run public-opinion validate-labels \
  --input data/model_io/raw_results_0001.jsonl \
  --output data/model_io/labels_validated_0001.jsonl \
  --failures-output data/model_io/labels_failures_0001.jsonl
```

### 4. 生成聚合报表

```bash
poetry run public-opinion aggregate \
  --input data/processed/comments_labeled.csv \
  --output-dir data/outputs
```

当前会输出：

- `stance_summary.csv`
- `sentiment_summary.csv`
- `topic_tags_summary.csv`

### 5. 一键跑通前半段流程

```bash
poetry run public-opinion run-pipeline --input remark.csv --output-dir data/run_001
```

如果同时提供 `--labels`，会继续输出合并后的评论表和聚合报表。

## 当前实现说明

- 为了降低首版依赖，主中间层使用 CSV，模型交换格式使用 JSONL。
- 若后续样本规模稳定达到百万级，建议升级到 Parquet 作为主分析格式。
- 低信息文本如 `顶`、`冲` 默认不导出到送模 JSONL，但会保留在规则打标后的评论表中。
- 模板复读文本默认只导出一个代表样本送模，合并阶段再把标签回填到同模板评论。
- OpenAI 兼容接口配置由 [config.py](/E:/vibecoding/PublicOpinionAnalytics/src/public_opinion/config.py:1) 统一加载，默认读取项目根目录 `.env`。
- `.env` 已加入 `.gitignore`，只提交 `.env.example`。
- 标签校验层会兼容少量常见格式漂移，例如 `negative -> 负面`、`against -> 反对官方处理`、`8 -> 高`，但仍建议优先通过 prompt 约束模型输出标准枚举。

## 测试

```bash
poetry run python -m unittest discover -s tests -v
```
