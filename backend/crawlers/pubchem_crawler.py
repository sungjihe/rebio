# backend/crawlers/pubchem_crawler.py
import requests

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


def fetch_pubchem_info(drug_name: str):
    """PubChem API에서 약물 기본 정보를 가져옵니다."""

    # 1) CID 조회
    cid_url = f"{PUBCHEM}/compound/name/{drug_name}/cids/JSON"
    cid_res = requests.get(cid_url, timeout=10)

    if cid_res.status_code != 200:
        return None

    cids = cid_res.json().get("IdentifierList", {}).get("CID", [])
    if not cids:
        return None

    cid = cids[0]

    # 2) 속성 조회
    detail_url = f"{PUBCHEM}/compound/cid/{cid}/property/IUPACName,CanonicalSMILES,InChIKey,MolecularWeight/JSON"
    detail_res = requests.get(detail_url, timeout=10)

    if detail_res.status_code != 200:
        return {"cid": cid}

    props = detail_res.json().get("PropertyTable", {}).get("Properties", [{}])[0]

    return {
        "cid": cid,
        "iupac": props.get("IUPACName"),
        "smiles": props.get("CanonicalSMILES"),
        "inchikey": props.get("InChIKey"),
        "mw": props.get("MolecularWeight")
    }
