#!/usr/bin/env python

import json
import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            obj = {
                "object": "np.array",
                "data": obj.tolist(),
                "dtype": obj.dtype.str,
                "shape": obj.shape,
            }
            return obj
        return super().default(obj)


class NumpyDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def decode(self, obj):
        obj = super().decode(obj)
        if isinstance(obj, dict):
            if obj.get("object", None) == "np.array":
                return np.array(obj["data"], dtype=obj["dtype"]).reshape(obj["shape"])
        return obj
