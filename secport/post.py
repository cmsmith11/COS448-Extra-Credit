from django.conf import settings
from .models import CONFESSION, COMMENT, REPLY
# from .models import SELF_HARM, VIOLENCE, SUBST_ABUSE, NSFW, SPOILER, OTHER
from PIL import Image, ImageDraw, ImageFont
import urllib.parse
import requests
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
import io

# graph explorer: https://developers.facebook.com/tools/explorer

def fb_prepare_content(post_info):
    sub_type = post_info['type']
    sub_num = str(post_info['sub_num'])
    cw = ''
    if post_info['cw'] != '' and sub_type == CONFESSION: # only confessions can get cws
        cw = 'cw: ' + post_info['cw'] + '\n•\n•\n•\n•\n'
    cleaned = '#' + sub_num + ': ' + cw + post_info['content']
    if post_info['as_op'] and sub_type != CONFESSION:
        cleaned = '[OP] ' + cleaned
    cleaned += '\n'
    if sub_type == CONFESSION:
        cleaned += '•\n•\n'
        #cleaned += str(post_info['dt_sub']) + '\n'
        cleaned += '----------------------------------------'
    cleaned += '------------------\n'
    verb = 'Comment' if sub_type == CONFESSION else 'Reply'
    cleaned += verb + ' anonymously: https://decentmod.herokuapp.com/'
    #cleaned += verb + ' anonymously: http://0.0.0.0:5000/'
    cleaned += urllib.parse.quote(post_info['group']) + '/' + sub_num
    return(cleaned)

# parent is page id for confessions
def fb_post(post_info):
    # post_info = { type, sub_num, as_op, cw, content, dt_sub, parent_id }
    URL = "https://graph.facebook.com/{}/".format(post_info['parent_id'])
    if post_info['type'] == CONFESSION:
        URL += 'feed'
    else:
        URL += 'comments'
    payload = {
        'message': fb_prepare_content(post_info),
        'access_token': post_info['token']
    }
    print('url:', URL)
    print('payload:', payload)
    r = requests.post(URL, data=payload) # possible point of failure
    print('response from FB:', r.text, flush=True)
    return(json.loads(r.text)['id'])

# returns formatted text (list of lines) and overflow for IG text image
def format_text(text, context, fnt, line_spacing, box_dims):
    box_w, box_h = box_dims
    lines = []
    cur_line = ''
    overflow = ''
    text.replace('\t', '    ')
    text = text.replace('\n', ' \n ')
    words = text.split(' ')
    i = 0
    # hold tight...
    _, words_h = context.textsize('ETAOINSHRDLU', font=fnt)
    candidate_h = (line_spacing * words_h) * (len(lines) + 1)
    while candidate_h < box_h and i < len(words):
        # room for another line. great.
        sp = ''
        candidate_w, _ = context.textsize(words[i], font=fnt)
        while candidate_w < box_w:
            # room for another word. great.
            cur_line += sp + words[i]
            i += 1
            sp = ' '
            if i >= len(words):
                break
            if words[i-1] == '\n':
                break
            candidate_w, _ = context.textsize(cur_line + sp + words[i], font=fnt)
        # uh oh... really long word case here
        if len(cur_line) == 0:
            fst = words[i]
            snd = ''
            while candidate_w >= box_w:
                snd = fst[-1] + snd
                fst = fst[:-1]
                candidate_w, _ = context.textsize(fst, font=fnt)
            words[i] = snd
            words.insert(i, fst)
        # add cur_line to lines
        if len(cur_line) > 0:
            lines.append(cur_line)
        cur_line = ''
        candidate_h = (line_spacing * words_h) * (len(lines) + 1)
    # add "..." to last line if needed
    if i < len(words):
        last_line = lines[-1]
        taken_off = ''
        last_w, _ = context.textsize(last_line + '...', font=fnt)
        while last_w > box_w:
            taken_off = last_line[last_line.rfind(' '):] + taken_off
            last_line = last_line[:last_line.rfind(' ')]
            last_w, _ = context.textsize(last_line + '...', font=fnt)
        lines[-1] = last_line + '...'
        overflow += taken_off
    # catches (rest of) overflow
    while i < len(words):
        overflow += ' ' + words[i]
        i += 1
    if len(overflow.strip()) > 0:
        overflow = '...' + overflow.strip()
    # return result in tuple
    return((lines, overflow))

def html_to_rbg(html):
    h = html[1:]
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# return public url of image and caption which may or may not contain overflow
def create_img(post_info):
    # img & text constants
    IMG_WIDTH = 1080
    IMG_HEIGHT = 1080
    MARGIN_WIDTH = 150
    MARGIN_HEIGHT = 150
    small_text_size = 35
    large_text_size = 60
    line_spacing = 1.5
    font_color = html_to_rbg(post_info['color']) #(231,117,0) # princeton orange
    # extract parameters
    img_content = ''
    if post_info['cw'] != '':
        img_content = 'cw: ' + post_info['cw']
    else:
        img_content = post_info['content']
    text = '#' + str(post_info['sub_num']) + ': ' + img_content
    dt = post_info['dt_sub']
    # begin creating image
    background = (255, 255, 255) # white
    img = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), background)
    # font
    font_size = small_text_size if len(text) > 80 else large_text_size
    fnt = ImageFont.truetype("secport/static/secport/Roboto-Regular.ttf", size=font_size)
    # handle text
    context = ImageDraw.Draw(img)
    box_w = IMG_WIDTH - 2 * MARGIN_WIDTH
    box_h = IMG_HEIGHT - 2 * MARGIN_HEIGHT
    lines, overflow = format_text(text, context, fnt, line_spacing, (box_w, box_h))
    # draw text
    _, line_height = context.textsize('ETAOINSHRDLU', font=fnt)
    line_height *= line_spacing
    top_offset = (IMG_HEIGHT - (len(lines) * line_height)) / 2
    for i, line in enumerate(lines):
        context.text((MARGIN_WIDTH, top_offset + (i * line_height)), line, font=fnt, fill=font_color)
    # date/time in lower right
    dt_fnt = ImageFont.truetype("secport/static/secport/Roboto-Regular.ttf", size=25)
    dt_width, dt_height = context.textsize(dt, font=dt_fnt)
    dt_left_offset = IMG_WIDTH - dt_width - 50
    dt_top_offset = IMG_HEIGHT - dt_height - 50
    context.text((dt_left_offset, dt_top_offset), dt, font=dt_fnt, fill=font_color)
    #img.show() # for debugging -- will remove
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    byte_img = buf.getvalue()
    cloud_response = cloudinary.uploader.upload(byte_img)
    # get url and caption
    img_url = cloud_response['secure_url']
    if post_info['cw'] != '':
        overflow = post_info['content']
    caption = '#' + str(post_info['sub_num']) + ': ' + overflow
    if len(overflow) > 0:
        caption += '\n•\n•\n'
    caption += 'Submit confession or comment anonymously using link in bio'
    caption += ' #' + post_info['group'].replace(' ', '_') + '_' + str(post_info['sub_num'])
    return((img_url, caption))

# handle either image or text case
def ig_prepare_content(post_info):
    if post_info['type'] == CONFESSION:
        img, cap = create_img(post_info)
        print('img:', img, flush=True)
        return((img, cap))
    else:
        content = '# ' + str(post_info['sub_num']) + ': ' + post_info['content']
        if post_info['as_op']:
            content = '[OP] ' + content
        return(content)

# parent is user id for confessions
def ig_post(post_info):
    print('post_info:', post_info)
    # post_info = { type, sub_num, as_op, cw, content, dt_sub, parent_id }
    sub_type = post_info['type']
    parent_id = post_info['parent_id']
    URL = "https://graph.facebook.com/{}/"
    # posting an image
    if sub_type == CONFESSION:
        img, cap = ig_prepare_content(post_info)
        payload = {
            'image_url': img,
            'caption': cap,
            'access_token': post_info['token']
        }
        r = requests.post(URL.format(parent_id) + 'media', data=payload)
        print('error request?:', r, flush=True)
        creation_id = json.loads(r.text)['id']
        payload = {
            'creation_id': creation_id,
            'access_token': post_info['token']
        }
        r = requests.post(URL.format(post_info['parent_id']) + 'media_publish', data=payload)
        return(json.loads(r.text)['id'])
    elif sub_type == COMMENT:
        URL = URL.format(parent_id) + 'comments'
    else:
        URL = URL.format(parent_id) + 'replies'
    payload = {
        'message': ig_prepare_content(post_info),
        'access_token': post_info['token']
    }
    r = requests.post(URL, data=payload)
    return(json.loads(r.text)['id'])

# temporary. Will submit accepted posts to TC# google form, with some extra info appended
def tc_post(post_info):
    # post_info = { type, sub_num, as_op, cw, content, dt_sub, parent_id }
    URL = 'https://docs.google.com/forms/d/1ukMa4ZT0-c2goyk-X12XxPm9Z4wEHbgZDCi2o70Fe2w/formResponse' # real url
    content = post_info['content']
    content += '\n•\n•\n•\n------\nThis post was submitted and pre-moderated through a Decent Mod™ portal.'
    payload = {
        'entry.362494257': content
    }
    try:
        print('[NOT] forwarding to TC#...', flush=True)
        #r = requests.post(URL, data=payload) # uncomment this to post to the ACTUAL TC# google form
        #print(r.status_code, '\n\n', r.text, flush=True)
    except:
        print('An error occurred posting to TC#', flush=True)

# test client
if __name__ == '__main__':
    long_text = "#49434: This is a 1080p test. Hopefully the picture looks a little less grainy. This is going to be a longer post than usual. It is a post, that is maybe about the longest size I could see it being. Maybe there's some limit--in fact there probably will be--but I don't know what that will be yet... who knows, but it isn't know. Hopefully this runs over. I think I should make it a bit longer. Because the font will be smaller, but at the same time I'm quite torn because I don't know how exactly long it should be... I suppose I'll want some overflow, but I don't know how much I need to write in order to do that. Like, I feel liek I have already written more than enough, but how can you know! You never do know. Interesting. This is a 1080p test. Hopefully the picture looks a little less grainy. This is going to be a longer post than usual. It is a post, that is maybe about the longest size I could see it being. Maybe there's some limit--in fact there probably will be--but I don't know what that will be yet... who knows, but it isn't know. Hopefully this runs over. I think I should make it a bit longer. Because the font will be smaller, but at the same time I'm quite torn because I don't know how exactly long it should be... I suppose I'll want some overflow, but I don't know how much I need to write in order to do that. Like, I feel liek I have already written more than enough, but how can you know! You never do know. Interesting."
    short_text = '#12345: This is short.'
    med_text = '#12345: This is an example confession. It\'s not too long, but not too short.'
    bug_text = '#12345: A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'
    img_path, overflow = create_img(long_text)
    print('overflow:', overflow)
    #upload_post(img_path, overflow)
