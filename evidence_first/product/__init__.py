"""Self-service product surface for Evidence-First."""

from .config import ProductConfig, default_config_path, load_config, save_config
from .providers import build_json_call, provider_readiness
from .sources import PreparedSources, prepare_sources
from .workspace import create_run_workspace, write_run_artifacts

__all__ = [
    "ProductConfig",
    "default_config_path",
    "load_config",
    "save_config",
    "build_json_call",
    "provider_readiness",
    "PreparedSources",
    "prepare_sources",
    "create_run_workspace",
    "write_run_artifacts",
]
