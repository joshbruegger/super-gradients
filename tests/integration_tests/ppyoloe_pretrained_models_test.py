import unittest
from typing import Mapping

import hydra.utils
import pkg_resources
from hydra import initialize_config_dir, compose
from hydra.core.global_hydra import GlobalHydra

import super_gradients
from super_gradients.training import MultiGPUMode
from super_gradients.training import Trainer
from super_gradients.training import models
from super_gradients.training.dataloaders.dataloaders import (
    detection_test_dataloader,
    get_new_data_loader,
)
from super_gradients.training.datasets import COCODetectionDataset
from super_gradients.training.metrics import DetectionMetrics
from super_gradients.training.models.detection_models.pp_yolo_e import PPYoloEPostPredictionCallback


class PPYoloEPretrainedModelsTest(unittest.TestCase):
    def setUp(self) -> None:
        super_gradients.init_trainer()

        self.coco_pretrained_ckpt_params = {"pretrained_weights": "coco"}

        self.coco_pretrained_maps = {
            "ppyoloe_s": 0.43,
        }

        self.transfer_detection_dataset = detection_test_dataloader()

    def test_pretrained_official_ppyoloe_s_coco(self):
        trainer = Trainer("ppyoloe_s", multi_gpu=MultiGPUMode.OFF)

        dataset_params = self.get_dataset_params("coco_detection_ppyoloe_dataset_params")
        dataset_params = hydra.utils.instantiate(dataset_params)

        test_loader = get_new_data_loader(
            dataset_cls=COCODetectionDataset, dataset_params=dataset_params.val_dataset_params, dataloader_params=dataset_params.val_dataloader_params
        )

        model = models.get("ppyoloe_s", **self.coco_pretrained_ckpt_params)
        res = trainer.test(
            model=model,
            test_loader=test_loader,
            test_metrics_list=[
                DetectionMetrics(
                    post_prediction_callback=PPYoloEPostPredictionCallback(score_threshold=0.1, nms_top_k=1000, nms_threshold=0.7, max_predictions=300),
                    num_cls=80,
                    normalize_targets=True,
                )
            ],
        )[2]
        self.assertAlmostEqual(res, self.coco_pretrained_maps["ppyoloe_s"], delta=0.001)

    def get_dataset_params(self, config_name, overriding_params: Mapping = None) -> Mapping:
        """
        Class for creating arch parameters dictionary, taking defaults from yaml
         files in src/super_gradients/recipes/arch_params.

        :param overriding_params: Dict, dictionary like object containing entries to override.
        :param config_name: arch_params yaml config filename in recipes (for example unet_default_arch_params).
        """
        if overriding_params is None:
            overriding_params = dict()
        GlobalHydra.instance().clear()
        with initialize_config_dir(config_dir=pkg_resources.resource_filename("super_gradients.recipes", "dataset_params/"), version_base="1.2"):
            cfg = compose(config_name=config_name)
            arch_params = hydra.utils.instantiate(cfg)
            arch_params.update(**overriding_params)
            return arch_params


if __name__ == "__main__":
    unittest.main()