#!/usr/bin/env python3
# Testing ig image creation
from PIL import Image, ImageDraw, ImageFont

# returns formatted text (list of lines) and overflow for IG text image
def format_text(text, context, fnt, line_spacing, box_dims):
    box_w, box_h = box_dims
    lines = []
    cur_line = ''
    overflow = ''
    text.replace('\t', '    ')
    text = text.replace('\n', ' \n ')
    words = text.split(' ')
    for i, w in enumerate(words):
        print('#'+str(i)+': |'+w+'|')
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
    font_color = (231,117,0) # princeton orange
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
    # fnt = ImageFont.truetype("secport/static/secport/Roboto-Regular.ttf", size=font_size)
    fnt = ImageFont.truetype("static/secport/Roboto-Regular.ttf", size=font_size)
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
    # dt_fnt = ImageFont.truetype("secport/static/secport/Roboto-Regular.ttf", size=25)
    dt_fnt = ImageFont.truetype("static/secport/Roboto-Regular.ttf", size=25)
    dt_width, dt_height = context.textsize(dt, font=dt_fnt)
    dt_left_offset = IMG_WIDTH - dt_width - 50
    dt_top_offset = IMG_HEIGHT - dt_height - 50
    context.text((dt_left_offset, dt_top_offset), dt, font=dt_fnt, fill=font_color)
    img.show() # for debugging -- will remove
    # buf = io.BytesIO()
    # img.save(buf, format='JPEG')
    # byte_img = buf.getvalue()
    # cloud_response = cloudinary.uploader.upload(byte_img)
    # # get url and caption
    # img_url = cloud_response['secure_url']
    # if post_info['cw'] != '':
    #     overflow = post_info['content']
    # caption = '#' + str(post_info['sub_num']) + ': ' + overflow
    # if len(overflow) > 0:
    #     caption += '\n•\n•\n'
    # caption += 'Submit confession or comment anonymously using link in bio'
    # caption += ' #' + post_info['group'].replace(' ', '_') + '_' + str(post_info['sub_num'])
    # return((img_url, caption))

####################################################################

print('starting...')
content = 'Dec    ent Mod 😃 is a to\n\n\nol used in conjunction with social media platforms to provide a way \
for users to engage in anonymously submitted, decentrally moderated content on public platforms.\
\n\n\nSome topics are hard to talk about. Sometimes you have no one to turn to. Sometimes there are \
things that you just need to get off your chest. There are countless reasons why a public platform \
which posts anonymous users\' submissions can be beneficial.'
post_info = {
    'group': 'Test Group',
    'type': 'confession',
    'sub_num': '38',
    'as_op': False,
    'cw': '',
    'content': content,
    'dt_sub': '12/30/22, 12:08pm'
}
create_img(post_info)
print('\n\n' + content)
