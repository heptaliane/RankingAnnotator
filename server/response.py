# -*- coding: utf-8 -*-
import base64
from typing import List, Tuple, Dict, Any

import numpy as np
import cv2
from nptyping import NDArray

from comparator import MatchComparator
from matching import MatchingGenerator


def _load_image(filename: str) -> NDArray[(Any, Any, 3), int]:
    return cv2.imread(filename, cv2.IMREAD_COLOR)


def _resize_image(img: NDArray[(Any, Any, 3), int],
                  max_size: int) -> NDArray[(Any, Any, 3), int]:
    h, w = img.shape[:2]
    ratio = max_size / max(h, w)

    if ratio > 1:
        return img

    dst_h, dst_w = int(h * ratio), int(w * ratio)
    return cv2.resize(img, (dst_w, dst_h))


def _encode_b64_image(img: NDArray[(Any, Any, 3), int]) -> str:
    ret, img = cv2.imencode('.jpg', img)

    if not ret:
        return None

    img = img.tostring()
    img = base64.encodebytes(img)
    return 'data:image/jpeg;base64,%s' % img.decode()


def _get_thumbnail(filename: str, max_size: int) -> str:
    img = _load_image(filename)
    img = _resize_image(img, max_size)
    return _encode_b64_image(img)


class ImageResponseIterator():
    def __init__(self, filenames: List[str],
                 comparator: MatchComparator,
                 matching: MatchingGenerator,
                 max_size: int = 400):
        self._names = filenames
        self._comparator = comparator
        self._rating = self._comparator.rating
        self._matching = matching
        self._max_size = max_size

    def _get_next_id(self) -> Tuple[int, int]:
        idx = next(self._matching)
        i1, i2 = np.argsort((self._rating[idx[0]], self._rating[idx[1]]))

        # Higher rating is first
        return (idx[i1].item(), idx[i2].item())

    def _get_image_response(self, idx: int) -> Dict:
        name = self._names[idx]
        thumb = _get_thumbnail(name, self._max_size)
        return {
            'id': idx,
            'rate': self._rating[idx].item(),
            'src': thumb,
        }

    def __next__(self) -> Dict:
        idx1, idx2 = self._get_next_id()

        return {
            'matches': {
                'total': self._comparator.n_match,
                'finished': self._comparator.n_finished,
            },
            'target': [
                self._get_image_response(idx1),
                self._get_image_response(idx2),
            ],
        }
