import requests
import re


class GoogleImgReverseSearch:
    @staticmethod
    def reverse_search(pic_url, filter_site=None, lang='en', region="US"):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'
        }
        hl_param = f"{lang}-{region}"
        params = {
            'image_url': pic_url,
            'hl': hl_param
        }
        response = requests.get('https://www.google.com/searchbyimage', params=params, allow_redirects=False)
        tbs_redirect = response.headers['location']
        tbs = requests.get(tbs_redirect, headers=headers)

        if filter_site is not None:
            filter_site = filter_site if 'www.' in filter_site else f'www.{filter_site}'
            default_q = re.search(b'title=".*?" value="(.*?)" ', tbs.content).group(1).decode("utf-8")
            params = {
                'q': f'{default_q} site:{filter_site}',
                'hl': hl_param
            }
            tbs_resp = requests.get(tbs_redirect, headers=headers, params=params)
        else:
            # tbs_resp = tbs
            raise NotImplementedError

        results_filtered = re.findall(f'href="(https://{filter_site}/.*?/)"'.encode(), tbs_resp.content, re.IGNORECASE)
        results = set(result.decode("utf-8") for result in results_filtered)

        return results
