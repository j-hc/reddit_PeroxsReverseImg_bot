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
# -------------------------------


def comment_parser(body):
    sub_filter = 'all'
    gallery_index = 0
    for n in body.split():
        if 'sub:' in n and len(n) >= 5:
            sub_filter = n[4:]
        elif 'gallery:' in n and len(n) >= 9:
            try:
                gallery_index = int(n[8:]) - 1
            except ValueError:
                pass
    return {'sub_filter': sub_filter, 'gallery_index': gallery_index}


def reply_builder(results, base_pic_url):
    image_hash_pair = {}
    hash_compare = CompareImageHashes(base_pic_url)
    for result in results:
        r_re = re.match(reddit_submission_regex, result)
        if r_re is not None:
            post_id = r_re.group(2)
        else:
            continue
        post_info = reverse_img_bot.get_info_by_id("t3_" + post_id)
        if post_info is None or not post_info.is_img:
            continue
        if post_info.is_gallery:
            img_url = post_info.gallery_media[0]
        else:
            img_url = post_info.url
        image_hash_pair.update({post_info: hash_compare.hamming_distance_percentage(img_url)})

    post_hash_pair_sorted = {post: hamming for post, hamming in sorted(image_hash_pair.items(), key=lambda item: item[1], reverse=True)}

    final_txt = []
    for post in post_hash_pair_sorted:
        posted_at = datetime.fromtimestamp(post.created_utc).strftime("%d/%m/%Y")
        post_direct = f"https://www.reddit.com{post.permalink}"
        sub = post.subreddit_name_prefixed
        post_title_truncated = post.title[:30]
        if len(post.title) > 30:
            post_title_truncated += "..."
        hamming = post_hash_pair_sorted[post]
        result_txt = f"- [{post_title_truncated}]({post_direct}) posted at {posted_at} in {sub} ({hamming})"
        final_txt.append(result_txt)
    return "\r\n\n".join(final_txt)


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
        results = GoogleImgReverseSearch.reverse_search(img_url, filter_site=filter_site, lang=post.lang)
        reply_built = reply_builder(results, img_url)
        comment_txt = ""
        if bool(reply_built):
            comment_txt += f"{lang_f['found_these']}\r\n\n{reply_built}"
        else:
            comment_txt = lang_f["nothing"]
        is_replied = reverse_img_bot.send_reply(comment_txt, notif)
        if is_replied != 0:
            sleep(is_replied)
            reverse_img_bot.send_reply(comment_txt, notif)

    elif notif.rtype == "comment_reply":
        # GOOD BOT
        if any(x in notif.body for x in good_bot_strs):
            reverse_img_bot.send_reply(lang_f['goodbot'], notif)


if __name__ == '__main__':
    reverse_img_bot = rBot(useragent, client_id, client_secret, bot_username, bot_pass)
    while True:
        notifs = reverse_img_bot.check_inbox(rkind='t1')
        for notif in notifs:
            reverse_img_bot.read_notifs(notif)
            notif_handler(notif)
        sleep(loop_interval)
