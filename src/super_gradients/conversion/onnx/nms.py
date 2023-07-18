import numpy as np
import onnx
import onnx_graphsurgeon as gs
from onnx import shape_inference

from super_gradients.common.abstractions.abstract_logger import get_logger

logger = get_logger(__name__)


def iteratively_infer_shapes(graph):
    """
    Sanitize the graph by cleaning any unconnected nodes, do a topological resort,
    and fold constant inputs values. When possible, run shape inference on the
    ONNX graph to determine tensor shapes.
    """
    logger.debug("Performing shape inference & folding.")
    for _ in range(3):
        count_before = len(graph.nodes)

        graph.cleanup().toposort()
        try:
            for node in graph.nodes:
                for o in node.outputs:
                    o.shape = None
            model = gs.export_onnx(graph)
            model = shape_inference.infer_shapes(model)
            graph = gs.import_onnx(model)
        except Exception as e:
            logger.debug(f"Shape inference could not be performed at this time:\n{e}")
        try:
            graph.fold_constants(fold_shapes=True)
        except TypeError as e:
            logger.error("This version of ONNX GraphSurgeon does not support folding shapes, " f"please upgrade your onnx_graphsurgeon module. Error:\n{e}")
            raise

        count_after = len(graph.nodes)
        if count_before == count_after:
            # No new folding occurred in this iteration, so we can stop for now.
            break
        logger.debug(f"Folded {count_before - count_after} constants.")


def attach_onnx_nms(
    onnx_model_path: str,
    output_onnx_model_path,
    detections_per_img: int,
    confidence_threshold: float,
    nms_threshold: float,
    precision: str = "fp32",
    batch_size: int = 1,
):
    """
    Attach ONNX NMS plugin to the ONNX model

    :param onnx_model_path:
    :param output_onnx_model_path:
    :param precision:
    :param batch_size:
    :return:
    """
    graph = gs.import_onnx(onnx.load(onnx_model_path))
    graph.fold_constants()

    # Do shape inference
    iteratively_infer_shapes(graph)

    pred_boxes, pred_scores = graph.outputs

    permute_scores = gs.Variable(
        name="permuted_scores",
        dtype=np.float32,
    )
    graph.layer(op="Transpose", name="permute_scores", inputs=[pred_scores], outputs=[permute_scores], attrs={"perm": [0, 2, 1]})

    op_inputs = [pred_boxes, permute_scores] + [
        gs.Constant(name="max_output_boxes_per_class", values=np.array([detections_per_img], dtype=np.int64)),
        gs.Constant(name="iou_threshold", values=np.array([nms_threshold], dtype=np.float32)),
        gs.Constant(name="score_threshold", values=np.array([confidence_threshold], dtype=np.float32)),
    ]
    logger.debug(f"op_inputs: {op_inputs}")

    # NMS Outputs
    # selected indices from the boxes tensor. [num_selected_indices, 3], the selected index format is [batch_index, class_index, box_index].
    output_selected_indices = gs.Variable(
        name="selected_indices",
        dtype=np.int64,
        # shape=[num_selected_indices, 3],
    )  # A scalar indicating the number of valid detections per batch image.

    op_outputs = [output_selected_indices]

    # Create the NMS Plugin node with the selected inputs. The outputs of the node will also
    # become the final outputs of the graph.
    graph.layer(
        op="NonMaxSuppression",
        name="batched_nms",
        inputs=op_inputs,
        outputs=op_outputs,
        attrs={
            "center_point_box": 0,
        },
    )

    if False:
        # graph.layer(op="GatherND", name="gather", inputs=[pred_boxes, boxes_indexes], outputs=[])
        # graph.layer(op="GatherND", name="gather", inputs=[pred_boxes, class_indexes], outputs=[])
        boxes_indexes = gs.Variable(
            name="boxes_indexes",
            dtype=np.int64,
        )

        graph.layer(
            op="Slice",
            name="take_boxes_indexes",
            inputs=[
                output_selected_indices,
                gs.Constant(name="take_boxes_indexes_start", values=np.array([0], dtype=np.int64)),
                gs.Constant(name="take_boxes_indexes_ends", values=np.array([2], dtype=np.int64)),
                gs.Constant(name="take_boxes_indexes_axes", values=np.array([1], dtype=np.int64)),
            ],
            outputs=[boxes_indexes],
            attrs={"axis": 1, "indices": [2]},
        )

        label_indexes = gs.Variable(
            name="label_indexes",
            dtype=np.int64,
        )
        graph.layer(op="Gather", name="take_label_indexes", inputs=[output_selected_indices], outputs=[label_indexes], attrs={"axis": 1, "indices": [2]})

        # select_classes = gs.Variable(
        #     name="select_classes",
        #     dtype=np.int64,
        # )

        # op_outputs = [output_selected_indices]

        # graph.layer(op="GatherND", name="gather", inputs=[pred_boxes, boxes_indexes], outputs=[])
        # graph.layer(op="GatherND", name="gather", inputs=[pred_boxes, class_indexes], outputs=[])

    graph.outputs = op_outputs

    iteratively_infer_shapes(graph)

    # Final cleanup & save
    graph.cleanup().toposort()
    model = gs.export_onnx(graph)
    onnx.save(model, output_onnx_model_path)
    logger.debug(f"Saved ONNX model to {output_onnx_model_path}")
