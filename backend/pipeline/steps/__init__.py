# backend/pipeline/steps/__init__.py

"""
Step-based data pipeline for ReBio.

각 step_* 모듈은 개별 파이프라인 단계를 담당:
- proteins
- therapeutic_proteins
- pdb
- diseases
- trials
- publications
- disgenet_merge
- relations
- graph
- embeddings
"""

from . import step_proteins
from . import step_therapeutic_proteins   # ★ NEW
from . import step_pdb
from . import step_diseases
from . import step_trials
from . import step_publications
from . import step_disgenet_merge
from . import step_relations
from . import step_graph
from . import step_embeddings
