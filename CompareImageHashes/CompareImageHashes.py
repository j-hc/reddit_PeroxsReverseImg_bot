from PIL import Image
import imagehash
import requests


class CompareImageHashes:
    def __init__(self, base_pic):
        self.base_img_hash = self._get_dhash_from_url(base_pic)

    def hamming_distance_percentage(self, pic2_url):
        hash2 = self._get_dhash_from_url(pic2_url)
        hamming_dist = hash2 - self.base_img_hash
        return 100.0 * (1.0 - hamming_dist / 64.0)

    def _get_raw_img(self, url):
        img = requests.get(url, stream=True)
        img.raw.decode_content = True
        return img.raw

    def _get_dhash_from_url(self, pic2_url):
        rawimg = self._get_raw_img(pic2_url)
        return imagehash.dhash(Image.open(rawimg))
