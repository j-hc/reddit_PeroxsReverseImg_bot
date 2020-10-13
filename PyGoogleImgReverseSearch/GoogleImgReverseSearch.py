import requests
import re


class GoogleImgReverseSearch:
    @staticmethod
    def reverse_search(pic_url, filter_site=None, lang='en', region="US"):
        if filter_site is None:
            raise NotImplementedError
        hl_param = f"{lang}-{region}"
        first_set_of_results = GoogleImgReverseSearch._perform_search(pic_url, hl_param, filter_site, 0)
        second_set_of_results = GoogleImgReverseSearch._perform_search(pic_url, hl_param, filter_site, 10)

        return first_set_of_results | second_set_of_results

    @staticmethod
    def _perform_search(pic_url, hl_param, filter_site, start):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/527.36 (KHTML, like Gecko) Chrome/84.0.4183.121 Safari/537.36'
        }
        params = {
            'image_url': pic_url,
            'hl': hl_param,
            'as_sitesearch': filter_site,
            'safe': 'images',
            'cr': '',
            'start': start
        }
        response = requests.get('https://www.google.com/searchbyimage', params=params, allow_redirects=False)
        tbs_response = requests.get(response.headers['location'], headers=headers, params={'hl': hl_param})

        results_filtered = re.findall(f'href="(https?://{filter_site}.*?)"'.encode(), tbs_response.content, re.IGNORECASE)
        results = set(result.decode("utf-8") for result in results_filtered)
        return results
