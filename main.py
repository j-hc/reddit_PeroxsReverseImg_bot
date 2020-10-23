from PyGoogleImgReverseSearch import GoogleImgReverseSearch
from rStuff import rBot
from info import useragent, client_id, client_secret, bot_username, bot_pass
from strings import tr, en
from time import sleep
import re
from CompareImageHashes import CompareImageHashes
from datetime import datetime


# Some stuff.. ------------------
good_bot_strs = ["good bot", "iyi bot", "güzel bot", "cici bot"]
loop_interval = 6
reddit_submission_regex = r"^https?://(www.)*reddit.com/r/.+?/comments/(.+?)/.*"

reverse_img_bot = rBot(useragent, client_id, client_secret, bot_username, bot_pass)
# -------------------------------


def comment_parser(body):
    sub_filter = 'all'
    gallery_index = 0
    for n in body.split():
        n_len = len(n)
        if 'sub:' in n and n_len >= 5:
            sub_filter = n[4:]
        elif 'gallery:' in n and n_len >= 9:
            try:
                gallery_index = int(n[8:]) - 1
            except ValueError:
                pass
    return {'sub_filter': sub_filter, 'gallery_index': gallery_index}


def reply_builder(results, base_pic_url, link_mode):
    if {'out_of_pages'} == results:
        return ''
    image_hash_pairs = []
    hash_compare = CompareImageHashes(base_pic_url)
    for submission_url, submission_img_url in results:
        r_re = re.match(reddit_submission_regex, submission_url)
        if r_re is not None:
            post_id = r_re.group(2)
        else:
            continue
        post_info = reverse_img_bot.get_info_by_id("t3_" + post_id)
        if post_info in list(sum(image_hash_pairs, ())) or post_info is None or not post_info.is_img or post_info.url.split('/')[-1] not in submission_img_url:
            continue
        if post_info.is_gallery:
            img_url = post_info.gallery_media[0]
        else:
            img_url = post_info.url
        image_hash_pairs.append((post_info, hash_compare.hamming_distance_percentage(img_url)))
    post_hash_pair_sorted = [(post, hamming) for post, hamming in sorted(image_hash_pairs, key=lambda item: item[1], reverse=True)][:6]
    final_txt = []
    for post, hamming in post_hash_pair_sorted:
        posted_at = datetime.fromtimestamp(post.created_utc).strftime("%d/%m/%Y")
        post_direct = f"https://{link_mode}.reddit.com{post.permalink}"
        sub = post.subreddit_name_prefixed
        post_title_truncated = post.title[:30]
        if len(post.title) > 30:
            post_title_truncated += "..."
        result_txt = f"- [{post_title_truncated}]({post_direct}) posted at {posted_at} in {sub} (%{hamming})"
        final_txt.append(result_txt)
    return "\r\n\n".join(final_txt)


def search_loop(img_url, filter_site, link_mode):
    at_least_one_reply = False
    start_pg_index = 0
    reply_built = ''
    while not at_least_one_reply and start_pg_index != 15:
        print(f"page {start_pg_index} to {start_pg_index + 3}")
        results = GoogleImgReverseSearch.reverse_search(pic_url=img_url, page_start=start_pg_index, page_end=start_pg_index + 3,
                                                        filter_site=filter_site, skip_same_img_ref=True)
        reply_built = reply_builder(results, img_url, link_mode)
        start_pg_index += 3
        at_least_one_reply = bool(reply_built)

        if 'out_of_pages' in results:
            break
    return reply_built


def notif_handler(notif):
    lang_f = tr if notif.lang == 'tr' else en
    if notif.rtype == 'username_mention':
        # NORMAL
        post = reverse_img_bot.get_info_by_id(notif.post_id)
        if not post.is_img:
            print("not an image")
            is_replied = reverse_img_bot.send_reply(lang_f["no_image"], notif)
            if is_replied != 0:
                sleep(is_replied)
                reverse_img_bot.send_reply(lang_f["no_image"], notif)
            return 0
        parsed_comment = comment_parser(notif.body)
        sub_filter, gallery_index = parsed_comment['sub_filter'], parsed_comment['gallery_index']
        if post.is_gallery:
            img_url = post.gallery_media[gallery_index % len(post.gallery_media)]
        else:
            img_url = post.url
        filter_site = f'www.reddit.com' if sub_filter == 'all' else f'www.reddit.com/r/{sub_filter}'
        print(f"searching for: {img_url} in {filter_site}")

        link_mode = "np" if notif.subreddit == "Turkey" else "www"
        reply_built = search_loop(img_url, filter_site, link_mode)

        if bool(reply_built):
            comment_txt = f"{lang_f['found_these']}\r\n\n{reply_built}"
        else:
            comment_txt = lang_f["nothing"]
        is_replied = reverse_img_bot.send_reply(comment_txt, notif)
        if is_replied != 0:
            sleep(is_replied)
            reverse_img_bot.send_reply(comment_txt, notif)

    elif notif.rtype == "comment_reply":
        # GOOD BOT
        if any(x in notif.body.lower() for x in good_bot_strs):
            reverse_img_bot.send_reply(lang_f['goodbot'], notif)


if __name__ == '__main__':
    while True:
        notifs = reverse_img_bot.check_inbox(rkind='t1')
        for notif in notifs:
            reverse_img_bot.read_notifs(notif)
            notif_handler(notif)
        sleep(loop_interval)
