import pytest
import logging
import hypothesis.strategies as st
from typing import Set, cast
from dataclasses import dataclass
from chromadb.api.types import IDs, ID
import chromadb.errors as errors
from chromadb.api import API
from chromadb.api.models.Collection import Collection
import chromadb.test.property.strategies as strategies
from hypothesis.stateful import (
    Bundle,
    RuleBasedStateMachine,
    MultipleResults,
    rule,
    initialize,
    precondition,
    consumes,
    run_state_machine_as_test,
    multiple,
    invariant,
)
from collections import defaultdict
import chromadb.test.property.invariants as invariants


traces: defaultdict[str, int] = defaultdict(lambda: 0)


def trace(key: str) -> None:
    global traces
    traces[key] += 1


def print_traces() -> None:
    global traces
    for key, value in traces.items():
        print(f"{key}: {value}")


dtype_shared_st: st.SearchStrategy = st.shared(
    st.sampled_from(strategies.float_types), key="dtype"
)
dimension_shared_st: st.SearchStrategy = st.shared(
    st.integers(min_value=2, max_value=2048), key="dimension"
)


@dataclass
class EmbeddingStateMachineStates:
    initialize = "initialize"
    add_embeddings = "add_embeddings"
    delete_by_ids = "delete_by_ids"
    update_embeddings = "update_embeddings"
    upsert_embeddings = "upsert_embeddings"


collection_st = st.shared(strategies.collections(with_hnsw_params=True), key="coll")


class EmbeddingStateMachine(RuleBasedStateMachine):  # type: ignore
    collection: Collection
    embedding_ids: Bundle = Bundle("embedding_ids")

    def __init__(self, api: API):
        super().__init__()
        self.api = api
        self._rules_strategy = strategies.DeterministicRuleStrategy(self)

    @initialize(collection=collection_st)  # type: ignore
    def initialize(self, collection: strategies.Collection):
        self.api.reset()
        self.collection = self.api.create_collection(
            name=collection.name,
            metadata=collection.metadata,
            embedding_function=collection.embedding_function,
        )
        self.embedding_function = collection.embedding_function
        trace("init")
        self.on_state_change(EmbeddingStateMachineStates.initialize)

        self.record_set_state = strategies.StateMachineRecordSet(
            ids=[], metadatas=[], documents=[], embeddings=[]
        )

    @rule(target=embedding_ids, record_set=strategies.recordsets(collection_st))  # type: ignore
    def add_embeddings(self, record_set: strategies.RecordSet) -> MultipleResults[ID]:
        trace("add_embeddings")
        self.on_state_change(EmbeddingStateMachineStates.add_embeddings)

        normalized_record_set: strategies.NormalizedRecordSet = invariants.wrap_all(
            record_set
        )

        if len(normalized_record_set["ids"]) > 0:
            trace("add_more_embeddings")

        if set(normalized_record_set["ids"]).intersection(
            set(self.record_set_state["ids"])
        ):
            with pytest.raises(errors.IDAlreadyExistsError):
                self.collection.add(**record_set)
            return multiple()
        else:
            self.collection.add(**record_set)
            self._upsert_embeddings(record_set)
            return multiple(*normalized_record_set["ids"])

    @precondition(lambda self: len(self.record_set_state["ids"]) > 20)  # type: ignore
    @rule(ids=st.lists(consumes(embedding_ids), min_size=1, max_size=20))  # type: ignore
    def delete_by_ids(self, ids: IDs):
        trace("remove embeddings")
        self.on_state_change(EmbeddingStateMachineStates.delete_by_ids)
        indices_to_remove = [self.record_set_state["ids"].index(id) for id in ids]

        self.collection.delete(ids=ids)
        self._remove_embeddings(set(indices_to_remove))

    # Removing the precondition causes the tests to frequently fail as "unsatisfiable"
    # Using a value < 5 causes retries and lowers the number of valid samples
    @precondition(lambda self: len(self.record_set_state["ids"]) >= 5)  # type: ignore
    @rule(
        record_set=strategies.recordsets(
            collection_strategy=collection_st,
            id_strategy=embedding_ids,
            min_size=1,
            max_size=5,
        )
    )  # type: ignore
    def update_embeddings(self, record_set: strategies.RecordSet):
        trace("update embeddings")
        self.on_state_change(EmbeddingStateMachineStates.update_embeddings)
        self.collection.update(**record_set)
        self._upsert_embeddings(record_set)

    # Using a value < 3 causes more retries and lowers the number of valid samples
    @precondition(lambda self: len(self.record_set_state["ids"]) >= 3)  # type: ignore
    @rule(
        record_set=strategies.recordsets(
            collection_strategy=collection_st,
            id_strategy=st.one_of(embedding_ids, strategies.safe_text),
            min_size=1,
            max_size=5,
        )
    )  # type: ignore
    def upsert_embeddings(self, record_set: strategies.RecordSet) -> None:
        trace("upsert embeddings")
        self.on_state_change(EmbeddingStateMachineStates.upsert_embeddings)
        self.collection.upsert(**record_set)
        self._upsert_embeddings(record_set)

    @invariant()  # type: ignore
    def count(self) -> None:
        invariants.count(
            self.collection, cast(strategies.RecordSet, self.record_set_state)
        )

    @invariant()  # type: ignore
    def no_duplicates(self) -> None:
        invariants.no_duplicates(self.collection)

    @invariant()  # type: ignore
    def ann_accuracy(self) -> None:
        invariants.ann_accuracy(
            collection=self.collection,
            record_set=cast(strategies.RecordSet, self.record_set_state),
            min_recall=0.95,
            embedding_function=self.embedding_function,
        )

    def _upsert_embeddings(self, record_set: strategies.RecordSet) -> None:
        normalized_record_set: strategies.NormalizedRecordSet = invariants.wrap_all(
            record_set
        )
        for idx, id in enumerate(normalized_record_set["ids"]):
            # Update path
            if id in self.record_set_state["ids"]:
                target_idx = self.record_set_state["ids"].index(id)
                if normalized_record_set["embeddings"] is not None:
                    self.record_set_state["embeddings"][
                        target_idx
                    ] = normalized_record_set["embeddings"][idx]
                else:
                    assert normalized_record_set["documents"] is not None
                    assert self.embedding_function is not None
                    self.record_set_state["embeddings"][
                        target_idx
                    ] = self.embedding_function(
                        [normalized_record_set["documents"][idx]]
                    )[
                        0
                    ]
                if normalized_record_set["metadatas"] is not None:
                    self.record_set_state["metadatas"][
                        target_idx
                    ] = normalized_record_set["metadatas"][idx]
                if normalized_record_set["documents"] is not None:
                    self.record_set_state["documents"][
                        target_idx
                    ] = normalized_record_set["documents"][idx]
            else:
                # Add path
                self.record_set_state["ids"].append(id)
                if normalized_record_set["embeddings"] is not None:
                    self.record_set_state["embeddings"].append(
                        normalized_record_set["embeddings"][idx]
                    )
                else:
                    assert self.embedding_function is not None
                    assert normalized_record_set["documents"] is not None
                    self.record_set_state["embeddings"].append(
                        self.embedding_function(
                            [normalized_record_set["documents"][idx]]
                        )[0]
                    )
                if normalized_record_set["metadatas"] is not None:
                    self.record_set_state["metadatas"].append(
                        normalized_record_set["metadatas"][idx]
                    )
                else:
                    self.record_set_state["metadatas"].append(None)
                if normalized_record_set["documents"] is not None:
                    self.record_set_state["documents"].append(
                        normalized_record_set["documents"][idx]
                    )
                else:
                    self.record_set_state["documents"].append(None)

    def _remove_embeddings(self, indices_to_remove: Set[int]) -> None:
        indices_list = list(indices_to_remove)
        indices_list.sort(reverse=True)

        for i in indices_list:
            del self.record_set_state["ids"][i]
            del self.record_set_state["embeddings"][i]
            del self.record_set_state["metadatas"][i]
            del self.record_set_state["documents"][i]

    def on_state_change(self, new_state: str) -> None:
        pass


def test_embeddings_state(caplog: pytest.LogCaptureFixture, api: API) -> None:
    caplog.set_level(logging.ERROR)
    run_state_machine_as_test(lambda: EmbeddingStateMachine(api))
    print_traces()


def test_multi_add(api: API) -> None:
    api.reset()
    coll = api.create_collection(name="foo")
    coll.add(ids=["a"], embeddings=[[0.0]])
    assert coll.count() == 1

    with pytest.raises(errors.IDAlreadyExistsError):
        coll.add(ids=["a"], embeddings=[[0.0]])

    assert coll.count() == 1

    results = coll.get()
    assert results["ids"] == ["a"]

    coll.delete(ids=["a"])
    assert coll.count() == 0


def test_dup_add(api: API) -> None:
    api.reset()
    coll = api.create_collection(name="foo")
    with pytest.raises(errors.DuplicateIDError):
        coll.add(ids=["a", "a"], embeddings=[[0.0], [1.1]])
    with pytest.raises(errors.DuplicateIDError):
        coll.upsert(ids=["a", "a"], embeddings=[[0.0], [1.1]])


# TODO: Use SQL escaping correctly internally
@pytest.mark.xfail(reason="We don't properly escape SQL internally, causing problems")  # type: ignore
def test_escape_chars_in_ids(api: API) -> None:
    api.reset()
    id = "\x1f"
    coll = api.create_collection(name="foo")
    coll.add(ids=[id], embeddings=[[0.0]])
    assert coll.count() == 1
    coll.delete(ids=[id])
    assert coll.count() == 0
