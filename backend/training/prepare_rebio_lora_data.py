import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

PROTEIN_FILE = os.path.join(RAW_DIR, "protein_redesign_examples.jsonl")
CLINICAL_FILE = os.path.join(RAW_DIR, "clinical_failure_examples.jsonl")
GRAPH_FILE = os.path.join(RAW_DIR, "graph_reasoning_examples.jsonl")

OUTPUT_FILE = os.path.join(PROCESSED_DIR, "rebio_lora_training.jsonl")


def load_jsonl(path):
    if not os.path.exists(path):
        print(f"[WARN] {path} 파일이 없습니다. 스킵합니다.")
        return []

    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"[ERROR] {path} JSONL 파싱 실패: {e}")
    return data


def convert_protein_redesign(samples):
    converted = []
    for ex in samples:
        seq = ex.get("sequence", "").strip()
        goal = ex.get("design_goal", "stability")
        answer = ex.get("answer", "").strip()

        if not seq or not answer:
            continue

        inst = "아래 단백질 서열에 대해 주어진 목표에 맞는 보수적 변이를 제안하고, 그 생물학적 근거를 설명하라."
        inp = f"Sequence: {seq}\nDesign goal: {goal}"

        converted.append({
            "task": "protein_redesign",
            "instruction": inst,
            "input": inp,
            "output": answer,
        })
    return converted


def convert_clinical_failure(samples):
    converted = []
    for ex in samples:
        drug = ex.get("drug_name", "").strip()
        summary = ex.get("trial_summary", "").strip()
        answer = ex.get("answer", "").strip()

        if not summary or not answer:
            continue

        inst = "다음 임상시험 요약을 기반으로 실패 이유를 분석하고, PK/PD 및 독성 관점에서 가능한 설명을 제시하라."
        inp = f"Drug: {drug}\n\nTrial summary:\n{summary}"

        converted.append({
            "task": "clinical_failure_analysis",
            "instruction": inst,
            "input": inp,
            "output": answer,
        })
    return converted


def convert_graph_reasoning(samples):
    converted = []
    for ex in samples:
        uid = ex.get("uniprot_id")
        cid = ex.get("candidate_id")
        path_json = ex.get("path_json")
        answer = ex.get("answer", "").strip()

        if not path_json or not answer:
            continue

        inst = "아래 Neo4j path JSON을 바탕으로, 단백질과 후보 질병/약물 사이의 생물학적 근거를 설명하라."
        inp = json.dumps({
            "uniprot_id": uid,
            "candidate_id": cid,
            "paths": path_json,
        }, ensure_ascii=False)

        converted.append({
            "task": "graph_evidence_reasoning",
            "instruction": inst,
            "input": inp,
            "output": answer,
        })
    return converted


def main():
    protein_raw = load_jsonl(PROTEIN_FILE)
    clinical_raw = load_jsonl(CLINICAL_FILE)
    graph_raw = load_jsonl(GRAPH_FILE)

    all_samples = []
    all_samples += convert_protein_redesign(protein_raw)
    all_samples += convert_clinical_failure(clinical_raw)
    all_samples += convert_graph_reasoning(graph_raw)

    print(f"[INFO] 변환된 샘플 수: {len(all_samples)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for ex in all_samples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"[INFO] 저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
