import torch
import json
import numpy as np
from typing import Dict, List
from comfy.model_base import CustomNode

class ParseqToDeforumNode(CustomNode):
    """
    A custom ComfyUI node that converts Parseq keyframe data into Deforum-compatible camera movements.
    """
    
    def __init__(self):
        super().__init__()
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "parseq_data": ("STRING", {"default": "{}"}),  # Expecting JSON string input
                "frame": ("INT", {"default": 0, "min": 0, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("DICT",)  # Output is a dictionary of Deforum-compatible camera params
    FUNCTION = "convert_parseq_to_deforum"
    CATEGORY = "Custom"
    
    def convert_parseq_to_deforum(self, parseq_data: str, frame: int):
        try:
            data = json.loads(parseq_data)  # Parse JSON string
            keyframes = data.get("keyframes", [])
            camera_params = self.extract_camera_params(keyframes, frame)
            return ({"camera_movement": camera_params},)
        except Exception as e:
            return ({"error": str(e)},)
    
    def extract_camera_params(self, keyframes: List[Dict], frame: int) -> Dict:
        """
        Extracts and interpolates camera movements from Parseq keyframes for the given frame.
        """
        params = {
            "translation_x": 0.0,
            "translation_y": 0.0,
            "translation_z": 0.0,
            "rotation_3d_x": 0.0,
            "rotation_3d_y": 0.0,
            "rotation_3d_z": 0.0,
            "zoom": 1.0,
        }
        
        frames = [kf["frame"] for kf in keyframes]
        
        if frame in frames:
            for kf in keyframes:
                if kf.get("frame") == frame:
                    for key in params.keys():
                        if key in kf:
                            params[key] = float(kf[key])
        else:
            params = self.interpolate_values(keyframes, frame, params)
        
        return params
    
    def interpolate_values(self, keyframes: List[Dict], frame: int, params: Dict) -> Dict:
        """
        Interpolates camera movement values for missing frames.
        """
        frames = np.array([kf["frame"] for kf in keyframes])
        prev_frame = frames[frames <= frame].max(initial=0)
        next_frame = frames[frames >= frame].min(initial=frame)
        
        prev_kf = next(kf for kf in keyframes if kf["frame"] == prev_frame)
        next_kf = next(kf for kf in keyframes if kf["frame"] == next_frame)
        
        alpha = (frame - prev_frame) / (next_frame - prev_frame + 1e-6)
        
        for key in params.keys():
            if key in prev_kf and key in next_kf:
                params[key] = (1 - alpha) * float(prev_kf[key]) + alpha * float(next_kf[key])
        
        return params

NODE_CLASS_MAPPINGS = {"ParseqToDeforum": ParseqToDeforumNode}
NODE_DISPLAY_NAME_MAPPINGS = {"ParseqToDeforum": "Parseq → Deforum Camera"}
