import copy
from typing import Union

from omegaconf import DictConfig

from super_gradients.common.object_names import Models
from super_gradients.common.registry import register_model
from super_gradients.training.models.arch_params_factory import get_arch_params
from super_gradients.training.models.detection_models.customizable_detector import CustomizableDetector
from super_gradients.training.utils import HpmStruct


@register_model(Models.DECIYOLO_S)
class DeciYolo_S(CustomizableDetector):
    def __init__(self, arch_params: Union[HpmStruct, DictConfig], in_channels: int = 3):
        default_arch_params = get_arch_params("deciyolo_s_arch_params")
        merged_arch_params = HpmStruct(**copy.deepcopy(default_arch_params))
        merged_arch_params.override(**arch_params.to_dict())
        super().__init__(merged_arch_params, in_channels=in_channels)

    @property
    def num_classes(self):
        return self.heads.num_classes


@register_model(Models.DECIYOLO_M)
class DeciYolo_M(CustomizableDetector):
    def __init__(self, arch_params: Union[HpmStruct, DictConfig], in_channels: int = 3):
        default_arch_params = get_arch_params("deciyolo_m_arch_params")
        merged_arch_params = HpmStruct(**copy.deepcopy(default_arch_params))
        merged_arch_params.override(**arch_params.to_dict())
        super().__init__(merged_arch_params, in_channels=in_channels)

    @property
    def num_classes(self):
        return self.heads.num_classes


@register_model(Models.DECIYOLO_L)
class DeciYolo_L(CustomizableDetector):
    def __init__(self, arch_params: Union[HpmStruct, DictConfig], in_channels: int = 3):
        default_arch_params = get_arch_params("deciyolo_l_arch_params")
        merged_arch_params = HpmStruct(**copy.deepcopy(default_arch_params))
        merged_arch_params.override(**arch_params.to_dict())
        super().__init__(merged_arch_params, in_channels=in_channels)

    @property
    def num_classes(self):
        return self.heads.num_classes