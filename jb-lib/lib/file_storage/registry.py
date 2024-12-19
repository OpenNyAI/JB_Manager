from typing import Dict, Type
from .storage import SyncStorage, AsyncStorage
from .local import LocalAsyncStorage, LocalSyncStorage
from .azure import AzureAsyncStorage, AzureSyncStorage
from .gcp import GcpAsyncStorage,GcpSyncStorage

STORAGE_REGISTRY: Dict[str, Type[AsyncStorage]] = {
    "local": LocalAsyncStorage,
    "azure": AzureAsyncStorage,
    "gcp": GcpAsyncStorage,
}

SYNC_STORAGE_REGISTRY: Dict[str, Type[SyncStorage]] = {
    "local": LocalSyncStorage,
    "azure": AzureSyncStorage,
    "gcp": GcpSyncStorage,
}
