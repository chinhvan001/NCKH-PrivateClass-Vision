from src.evaluation.person_detection import BoundingBox, combine_metrics, evaluate_boxes, iou


def test_iou_and_one_to_one_matching():
    truth = [BoundingBox(0, 0, 10, 10), BoundingBox(20, 20, 30, 30)]
    predicted = [BoundingBox(0, 0, 10, 10), BoundingBox(0, 0, 10, 10), BoundingBox(20, 20, 30, 30)]
    assert iou(predicted[0], truth[0]) == 1.0
    metric = evaluate_boxes(predicted, truth)
    assert (metric.true_positive, metric.false_positive, metric.false_negative) == (2, 1, 0)
    assert metric.recall == 1.0


def test_combine_metrics_computes_dataset_level_recall():
    metric = combine_metrics([evaluate_boxes([BoundingBox(0, 0, 5, 5)], [BoundingBox(0, 0, 5, 5)]), evaluate_boxes([], [BoundingBox(0, 0, 5, 5)])])
    assert (metric.true_positive, metric.false_positive, metric.false_negative) == (1, 0, 1)
    assert metric.recall == 0.5
