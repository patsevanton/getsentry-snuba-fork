from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Generic, Optional, Sequence, TypeVar

import sentry_sdk

from snuba import settings as snuba_settings
from snuba.clickhouse.query import Query
from snuba.clusters.cluster import ClickhouseCluster
from snuba.clusters.storage_sets import StorageSetKey
from snuba.datasets.entities.storage_selectors import QueryStorageSelector
from snuba.datasets.entities.storage_selectors.selector import QueryStorageSelectorError
from snuba.datasets.plans.cluster_selector import ColumnBasedStorageSliceSelector
from snuba.datasets.plans.translator.query import QueryTranslator
from snuba.datasets.schemas import RelationalSource
from snuba.datasets.schemas.tables import TableSource
from snuba.datasets.slicing import is_storage_set_sliced
from snuba.datasets.storage import (
    EntityStorageConnection,
    ReadableStorage,
    ReadableTableStorage,
    StorageNotAvailable,
)
from snuba.datasets.storages.factory import get_storage
from snuba.datasets.storages.storage_key import StorageKey
from snuba.pipeline.utils.storage_finder import StorageKeyFinder
from snuba.query import Query as AbstractQuery
from snuba.query.allocation_policies import AllocationPolicy
from snuba.query.data_source.simple import Table
from snuba.query.logical import Query as LogicalQuery
from snuba.query.processors.physical import ClickhouseQueryProcessor
from snuba.query.processors.physical.conditions_enforcer import (
    MandatoryConditionEnforcer,
)
from snuba.query.processors.physical.mandatory_condition_applier import (
    MandatoryConditionApplier,
)
from snuba.query.query_settings import QuerySettings
from snuba.state import explain_meta
from snuba.utils.metrics.util import with_span

TQuery = TypeVar("TQuery", bound=AbstractQuery)


@dataclass(frozen=True)
class QueryPlanNew(ABC, Generic[TQuery]):
    """
    Provides the directions to execute a Clickhouse Query against one
    storage or multiple joined ones.

    This is produced in the storage processing stage of the query pipeline.

    It embeds the Clickhouse Query (the query to run on the storage
    after translation). It also provides a plan execution strategy
    that takes care of coordinating the execution of the query against
    the database.

    When running a query we need a cluster, the cluster is picked according
    to the storages sets containing the storages used in the query.
    So the plan keeps track of the storage set as well.
    There must be only one storage set per query.
    """

    query: TQuery
    storage_set_key: StorageSetKey


@dataclass(frozen=True)
class ClickhouseQueryPlanNew(QueryPlanNew[Query]):
    """
    Query plan for a single entity, single storage query.

    It provides the sequence of storage specific QueryProcessors
    to apply to the query after the the storage has been selected.
    These are divided in two sequences: plan processors and DB
    processors.
    Plan processors and DB Query Processors are both executed only
    once per plan.
    """

    # Per https://github.com/python/mypy/issues/10039, this has to be redeclared
    # to avoid a mypy error.
    plan_query_processors: Sequence[ClickhouseQueryProcessor]
    db_query_processors: Sequence[ClickhouseQueryProcessor]


def get_query_data_source(
    relational_source: RelationalSource,
    allocation_policies: list[AllocationPolicy],
    final: bool,
    sampling_rate: Optional[float],
    storage_key: StorageKey,
) -> Table:
    assert isinstance(relational_source, TableSource)
    return Table(
        table_name=relational_source.get_table_name(),
        schema=relational_source.get_columns(),
        allocation_policies=allocation_policies,
        final=final,
        sampling_rate=sampling_rate,
        mandatory_conditions=relational_source.get_mandatory_conditions(),
        storage_key=storage_key,
    )


class EntityProcessingExecutor:
    """
    An executor for applying everything related to entity processing to a query.
    This executor applies the following processing steps:
        1. Applies entity processors defined on the entity
        2. Selects a storage based on the storage selector
        3. Applies translation mappers
        4. Translates the logical query to physical query
    """

    def __init__(
        self,
        storages: Sequence[EntityStorageConnection],
        selector: QueryStorageSelector,
        post_processors: Optional[Sequence[ClickhouseQueryProcessor]] = None,
        partition_key_column_name: Optional[str] = None,
    ) -> None:
        # A list of storages and the translation mappers they are associated with.
        # This list will only contain one storage and mappers for single storage entities.
        # If there are more than one storage and mappers, a selector is required
        self.__storages = storages
        # A storage selector class to determine which to use in query plan
        self.__selector = selector
        # This is a set of query processors that have to be executed on the
        # query after the storage selection but that are defined by the dataset.
        # Query processors defined by a Storage must be executable independently
        # from the context the Storage is used (whether the storage is used by
        # itself or whether it is joined with another storage).
        # In a joined query we would have processors defined by multiple storages.
        # that would have to be executed only once (like Prewhere). That is a
        # candidate to be added here as post process.
        self.__post_processors = post_processors or []
        self.__partition_key_column_name = partition_key_column_name

    def get_storage(
        self, query: LogicalQuery, settings: QuerySettings
    ) -> EntityStorageConnection:
        with sentry_sdk.start_span(
            op="build_plan.storage_query_plan_builder", description="select_storage"
        ):
            return self.__selector.select_storage(query, settings, self.__storages)

    def get_cluster(
        self, storage: ReadableStorage, query: LogicalQuery, settings: QuerySettings
    ) -> ClickhouseCluster:
        if is_storage_set_sliced(storage.get_storage_set_key()):
            with sentry_sdk.start_span(
                op="build_plan.sliced_storage", description="select_storage"
            ):
                assert (
                    self.__partition_key_column_name is not None
                ), "partition key column name must be defined for a sliced storage"
                assert isinstance(storage, ReadableTableStorage)
                return ColumnBasedStorageSliceSelector(
                    storage=storage.get_storage_key(),
                    storage_set=storage.get_storage_set_key(),
                    partition_key_column_name=self.__partition_key_column_name,
                ).select_cluster(query, settings)
        return storage.get_cluster()

    def translate_query_and_apply_mappers(
        self, query: LogicalQuery, settings: QuerySettings
    ) -> Query:
        if len(self.__storages) < 1:
            raise QueryStorageSelectorError("No storages specified to select from.")
        storage_connection = self.get_storage(query, settings)
        storage = storage_connection.storage
        mappers = storage_connection.translation_mappers

        check_storage_readiness(storage)

        with sentry_sdk.start_span(
            op="build_plan.storage_query_plan_builder", description="translate"
        ):
            # The QueryTranslator class should be instantiated once for each call to
            # translate_query_and_apply_mappers to avoid cache conflicts.
            clickhouse_query = QueryTranslator(mappers).translate(query)

        with sentry_sdk.start_span(
            op="build_plan.storage_query_plan_builder", description="set_from_clause"
        ):
            clickhouse_query.set_from_clause(
                get_query_data_source(
                    storage.get_schema().get_data_source(),
                    allocation_policies=storage.get_allocation_policies(),
                    final=query.get_final(),
                    sampling_rate=query.get_sample(),
                    storage_key=storage.get_storage_key(),
                )
            )

        if settings.get_dry_run():
            explain_meta.add_transform_step(
                "storage_planning", "mappers", str(query), str(clickhouse_query)
            )

        return clickhouse_query

    def execute(self, query: LogicalQuery, settings: QuerySettings) -> Query:
        from snuba.pipeline.processors import execute_entity_processors

        execute_entity_processors(query, settings)
        return self.translate_query_and_apply_mappers(query, settings)


def check_storage_readiness(storage: ReadableStorage) -> None:
    # Return failure if storage readiness state is not supported in current environment
    if snuba_settings.READINESS_STATE_FAIL_QUERIES:
        assert isinstance(storage, ReadableTableStorage)
        readiness_state = storage.get_readiness_state()
        if readiness_state.value not in snuba_settings.SUPPORTED_STATES:
            raise StorageNotAvailable(
                StorageNotAvailable.__name__,
                f"The selected storage={storage.get_storage_key().value} is not available in this environment yet. To enable it, consider bumping the storage's readiness_state.",
            )


def build_best_plan(
    clickhouse_query: Query,
    settings: QuerySettings,
    post_processors: Sequence[ClickhouseQueryProcessor] = [],
) -> ClickhouseQueryPlanNew:
    storage_key = StorageKeyFinder().visit(clickhouse_query)
    storage = get_storage(storage_key)

    # Return failure if storage readiness state is not supported in current environment
    check_storage_readiness(storage)

    db_query_processors = [
        *storage.get_query_processors(),
        *post_processors,
        MandatoryConditionApplier(),
        MandatoryConditionEnforcer(storage.get_mandatory_condition_checkers()),
    ]

    return ClickhouseQueryPlanNew(
        query=clickhouse_query,
        plan_query_processors=[],
        db_query_processors=db_query_processors,
        storage_set_key=storage.get_storage_set_key(),
    )


@with_span()
def apply_storage_processors(
    query_plan: ClickhouseQueryPlanNew,
    settings: QuerySettings,
    post_processors: Sequence[ClickhouseQueryProcessor] = [],
) -> Query:
    # storage selection should not be done through the entity anymore.
    storage_key = StorageKeyFinder().visit(query_plan.query)
    storage = get_storage(storage_key)
    if is_storage_set_sliced(storage.get_storage_set_key()):
        raise NotImplementedError("sliced storages not supported in new pipeline")

    check_storage_readiness(storage)

    with sentry_sdk.start_span(
        op="build_plan.storage_query_plan_builder", description="set_from_clause"
    ):
        query_plan.query.set_from_clause(
            get_query_data_source(
                storage.get_schema().get_data_source(),
                allocation_policies=storage.get_allocation_policies(),
                final=query_plan.query.get_from_clause().final,
                sampling_rate=query_plan.query.get_from_clause().sampling_rate,
                storage_key=storage.get_storage_key(),
            )
        )

    for processor in query_plan.db_query_processors:
        with sentry_sdk.start_span(
            description=type(processor).__name__, op="processor"
        ):
            if settings.get_dry_run():
                with explain_meta.with_query_differ(
                    "storage_processor", type(processor).__name__, query_plan.query
                ):
                    processor.process_query(query_plan.query, settings)
            else:
                processor.process_query(query_plan.query, settings)

    return query_plan.query
