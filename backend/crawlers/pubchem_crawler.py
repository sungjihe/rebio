# backend/crawlers/pubchem_crawler.py

from backend.crawlers.common import safe_get

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"

def fetch_pubchem_info(drug_name: str):
    """PubChem Drug Info"""

    # 1) CID 조회
    cid_url = f"{PUBCHEM}/compound/name/{drug_name}/cids/JSON"
    cid_res = safe_get(cid_url)

    if not cid_res:
        return {
            "ok": False,
            "source": "pubchem",
            "data": None,
            "error": "cid_lookup_failed"
        }

    cids = cid_res.json().get("IdentifierList", {}).get("CID", [])
    if not cids:
        return {
            "ok": False,
            "source": "pubchem",
            "data": None,
            "error": "no_cid_found"
        }

    cid = cids[0]

    # 2) 속성 조회
    detail_url = (
        f"{PUBCHEM}/compound/cid/{cid}/property/"
        "IUPACName,CanonicalSMILES,InChIKey,MolecularWeight/JSON"
    )

    detail_res = safe_get(detail_url)

    if not detail_res:
        return {
            "ok": True,
            "source": "pubchem",
            "data": {"cid": cid},
            "error": "property_fetch_failed"
        }

    props = detail_res.json().get("PropertyTable", {}).get("Properties", [{}])[0]

    return {
        "ok": True,
        "source": "pubchem",
        "data": {
            "cid": cid,
            "iupac": props.get("IUPACName"),
            "smiles": props.get("CanonicalSMILES"),
            "inchikey": props.get("InChIKey"),
            "mw": props.get("MolecularWeight"),
        },
        "error": None,
    }
