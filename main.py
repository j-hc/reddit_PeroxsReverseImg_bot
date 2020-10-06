from PyGoogleImgReverseSearch import GoogleImgReverseSearch
from rStuff import rBot, rPost
from info import useragent, client_id, client_secret, bot_username, bot_pass
from strings import tr, en
from time import sleep


# Some stuff.. ------------------
good_bot_strs = ["good bot", "iyi bot", "güzel bot", "cici bot"]
loop_interval = 6
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


def reply_builder(results):
    self_text_posts_l = []
    image_posts_l = []
    for result in results:
        if "/r/" in result:
            try:
                post_id = result.split('/')[6]
            except IndexError:
                continue
            post_req = reverse_img_bot.get_info_by_id("t3_" + post_id)
            if post_req is not None:
                post_info = rPost(post_req)
            else:
                continue
            result_txt = f"- [{post_info.title}]({result}) from {post_info.subreddit_name_prefixed}"
            if post_info.is_img:
                image_posts_l.append(result_txt)
            else:
                self_text_posts_l.append(result_txt)
    self_text_posts = "\r\n\n".join(self_text_posts_l)
    image_posts = "\r\n\n".join(image_posts_l)
    return {"self_text_posts": self_text_posts, "image_posts": image_posts}


def notif_handler(notif):
    lang_f = tr if notif.lang == 'tr' else en
    if notif.rtype == 'username_mention':
        # NORMAL
        post = rPost(reverse_img_bot.get_info_by_id(notif.post_id))
        if not post.is_img:
            print("not an image")
            is_replied = reverse_img_bot.send_reply(lang_f["no-image"], notif)
            if is_replied != 0:
                sleep(is_replied)
                reverse_img_bot.send_reply(lang_f["no-image"], notif)
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
        reply_built = reply_builder(results)
        image_posts = reply_built["image_posts"]
        self_text_posts = reply_built["self_text_posts"]
        comment_txt = ""
        if bool(image_posts):
            comment_txt += f"{lang_f['found_these']}\r\n\n{image_posts}"
        if bool(self_text_posts):
            comment_txt += f"\r\n\n{lang_f['maybe_relevant']}\r\n\n{self_text_posts}"
        if not bool(comment_txt):
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
