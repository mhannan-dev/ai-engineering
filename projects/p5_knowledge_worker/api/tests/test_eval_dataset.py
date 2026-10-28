"""Tests for evaluation dataset integrity and schema."""


from knowledge_worker.evaluation.dataset import get_default_dataset_path, load_eval_dataset


def test_eval_dataset_file_exists():
    path = get_default_dataset_path()
    assert path.exists(), f"Default dataset file does not exist at {path}"


def test_load_eval_dataset():
    dataset = load_eval_dataset()
    assert len(dataset) >= 30, f"Expected at least 30 eval queries, found {len(dataset)}"


def test_categories_coverage():
    dataset = load_eval_dataset()
    categories = {q.category for q in dataset}
    expected = {"english", "bangla", "cross_lingual", "banglish", "unanswerable"}
    assert expected.issubset(categories), f"Missing categories: {expected - categories}"


def test_answerable_queries_consistency():
    dataset = load_eval_dataset()
    for q in dataset:
        if q.is_answerable:
            assert q.expected_doc is not None, f"Query {q.id} missing expected_doc"
            assert q.expected_heading is not None, f"Query {q.id} missing expected_heading"
            assert q.expected_fact is not None, f"Query {q.id} missing expected_fact"
            assert len(q.relevance_grades) > 0, f"Query {q.id} missing relevance grades"
            for grade in q.relevance_grades:
                assert 1 <= grade.grade <= 3, f"Query {q.id} invalid grade {grade.grade}"
        else:
            assert q.expected_doc is None, f"Unanswerable query {q.id} should not have expected_doc"
            assert len(q.relevance_grades) == 0, f"Unanswerable query {q.id} should not have grades"


def test_referenced_documents_exist():
    dataset = load_eval_dataset()
    dataset_path = get_default_dataset_path()
    p5_root = dataset_path.parents[1]

    for q in dataset:
        if q.expected_doc:
            doc_in_sample = p5_root / "sample_documents" / q.expected_doc
            doc_in_root = p5_root / q.expected_doc
            assert doc_in_sample.exists() or doc_in_root.exists(), (
                f"Referenced document '{q.expected_doc}' for query {q.id} not found on disk"
            )
