import csv
import json
from collections import Counter
from pathlib import Path

ruled_path = Path("E:/vibecoding/PublicOpinionAnalytics/data/ruled_90w.csv")
model_path = Path("E:/vibecoding/PublicOpinionAnalytics/data/model_input_90w.jsonl")

# Stats from ruled CSV
total = 0
empty_text = 0
short_text = 0
low_info = 0
template_text = 0
mobilization = 0
priority_counts = Counter()
topic_counts = Counter()
risk_counts = Counter()

with ruled_path.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        total += 1
        if row.get("is_empty_text") == "true":
            empty_text += 1
        if row.get("is_short_text") == "true":
            short_text += 1
        if row.get("is_low_info") == "true":
            low_info += 1
        if row.get("is_template_text") == "true":
            template_text += 1
        if row.get("is_mobilization") == "true":
            mobilization += 1
        priority_counts[row.get("analysis_priority", "")] += 1
        for tag in json.loads(row.get("rule_topic_tags", "[]")):
            topic_counts[tag] += 1
        for tag in json.loads(row.get("rule_risk_tags", "[]")):
            risk_counts[tag] += 1

# Stats from model input
model_total = 0
canonical_groups = set()
with model_path.open("r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        model_total += 1
        row = json.loads(line)
        tg = row.get("template_group", "")
        if tg:
            canonical_groups.add(tg)

out = []
out.append(f"=== 全量数据统计 (remark-90w) ===")
out.append(f"总记录数:        {total:,}")
out.append(f"空文本:          {empty_text:,}")
out.append(f"短文本(<=4字):   {short_text:,}")
out.append(f"低信息量:        {low_info:,}")
out.append(f"模板文本(重复):  {template_text:,}")
out.append(f"含动员关键词:    {mobilization:,}")
out.append(f"")
out.append(f"=== 优先级分布 ===")
for k, v in priority_counts.most_common():
    out.append(f"  {k}: {v:,}")
out.append(f"")
out.append(f"=== 规则 topic_tags 分布 ===")
for k, v in topic_counts.most_common():
    out.append(f"  {k}: {v:,}")
out.append(f"")
out.append(f"=== 规则 risk_tags 分布 ===")
for k, v in risk_counts.most_common():
    out.append(f"  {k}: {v:,}")
out.append(f"")
out.append(f"=== LLM 标注规模 ===")
out.append(f"待标注(model_input): {model_total:,}")
out.append(f"归一化模板组数:      {len(canonical_groups):,}")
out.append(f"压缩比:              {total}/{model_total} = {total/max(model_total,1):.1f}x")

result = "\n".join(out)
print(result)
Path("E:/vibecoding/PublicOpinionAnalytics/data/stats_90w.txt").write_text(result, encoding="utf-8")
