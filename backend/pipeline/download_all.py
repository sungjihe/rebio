from .protein_downloader import download_proteins
from .drug_downloader import download_drugs
from .diseases_downloader import download_diseases
from .trials_downloader import download_trials
from .publications_downloader import download_publications

PROTEINS = ["P04637", "P38398"]  
DRUGS = ["Doxorubicin", "Erlotinib"]  
DISEASES = ["breast cancer", "lung adenocarcinoma"]  

def main():
    download_proteins(PROTEINS)
    download_drugs(DRUGS)
    download_diseases(DISEASES)
    download_trials(DRUGS)
    download_publications(DISEASES)

if __name__ == "__main__":
    main()
