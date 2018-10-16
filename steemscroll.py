#!/usr/bin/env python
# coding=utf-8

# most of the work was done by sconemad:
# https://github.com/sconemad/unicorn-scroller
# >original<
# unicorn-scroller - A scrolling information display for the
# Pimoroni Unicorn HAT/PHAT on Raspberry Pi.
#
# By Andrew Wedgbury <wedge@sconemad.com>

# customized by tibfox to show steemit related data for a specific account

import unicornhat as unicorn
from PIL import ImageFont, ImageColor, ImageDraw, ImageFilter, Image
import time, re

# DISPLAY SETTINGS #

# orientation of the displayed content (0,90,180,270) | 180 = power cable is on the bottom left corner
unicorn.rotation(180)

# Display brightness (0...1, 1 is very very very bright)
brightness_min = 0.3
brightness_max = 0.6
estimate_brightness = 1 # device sensor is turned on

# Pause between steps in seconds, defines the scroll speed
global_speed = 0.06

# Background colour
back='DarkSlateGray'

unicorn.set_layout(unicorn.PHAT)
geom = unicorn.get_shape()
if (geom[0] != geom[1]):
    unicorn.set_layout([
        [0 , 1 , 2 , 3 , 4 , 5 , 6 , 7 ],
        [8 , 9 , 10, 11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20, 21, 22, 23],
        [24, 25, 26, 27, 28, 29, 30, 31]
    ])
    global_speed *=2


# FONT SETTINGS #

# Font for displaying text (you can use your desired fonts) 
font = ImageFont.truetype("8-bit_fortress.ttf",7)

# default font offset | If you use your own fonts you probably need to adjust this
font_offset = 0


# STEEM SETTINGS #

# Do we want to load (long time) and display steem content or 
# just want to test out stuff from test_output() ? False = test_ouput()
connect_steem = True 

# import neccesary libraries and set account for scroll data
if(connect_steem):
    from beem import Steem
    from beem.account import Account
    from beem.comment import Comment
    acc = Account("tibfox") # change this to your desired steemit account
    steem = Steem()

def set_brightness(pc):
        b = brightness_min + ((brightness_max - brightness_min) * pc / 100.0)
        if (b > brightness_max): b = brightness_max
        if (b < brightness_min): b = brightness_min
        unicorn.brightness(b)

def get_item_size(item):
    width = 1
    frames = 1
    if ('text' in item):
        width += font.getsize(item['text'])[0]
    elif ('image' in item):
        width += item['image'].size[0]
        frames = item['image'].size[1] / 8
    return width,frames

def get_size(items):
    width = 0
    frames = 1
    for item in items:
        w,f = get_item_size(item)
        width += w
        frames = max(f, frames)
    return width,frames

def render(items):
    width,frames = get_size(items)
    image = Image.new('RGB', (width,8), back)
    pos = 0
    for item in items:
        w,f = get_item_size(item)
        if ('text' in item):
            draw = ImageDraw.Draw(image)
            draw.text((pos, font_offset), item['text'], font=font, fill=item['fore'])
        elif ('image' in item):
            image.paste(item['image'], (pos,0))
        pos += w
    
    return image

def scroll(image):
    width,height = image.size
    for offset in range(-geom[1],width):
        for x in range(geom[1]):
            for y in range(8):
                if ((x+offset < 0) | (x+offset >= width)):
                    r,g,b = ImageColor.getrgb(back)
                else:
                    r, g, b = image.getpixel((x+offset,y))
                unicorn.set_pixel(x,y, r,g,b)
        unicorn.show()
        time.sleep(global_speed)

def process_line(l):
    global colour
    items = []
    global estimate_brightness
    m = re.match(r'^colou?r: *(.+) *$', l)
    if (m):
        try:
            c = ImageColor.getrgb(m.group(1))
            colour = m.group(1)
        except ValueError:
            print("error color unknown")
            colour = 'white'
        return

    m = re.match(r'^text:(.+)$', l)
    if (m):
        return {'text':m.group(1), 'fore':colour}

    m = re.match(r'^image:(.+)$', l)
    if (m):
        try:
            im = Image.open('images/' + m.group(1))
            return {'image':im}
        except IOError:
            return {'text:<?%s?>' % (m.group(1))}
        return

    m = re.match(r'^estimated-brightness: *(\d+) *$', l)
    if (m and estimate_brightness):
        set_brightness(int(m.group(1)))
        return

    m = re.match(r'^measured-brightness: *(\d+) *$', l)
    if (m):
        set_brightness(int(m.group(1)))
        # Disable brightness estimation if measured
        estimate_brightness = 0
        return


def print_time(): #testing stuff
    items = []
    t = time.localtime()
    process_line("colour:Limegreen")
    items.append(process_line("text:test TEST"))
    image = render(items)
    scroll(image)
    return


if connect_steem: 
    def mana_bars(): # show blue vp and green rc bar
        unicorn.clear()

        # check voting mana
        vp_mana = round(8/100*acc.get_voting_power(with_regeneration=True))
        rc_mana = round(8/100*acc.get_rc_manabar()['estimated_pct'])
    
        # print mana in pixels
        for y in range(8):
            for x in range(2):
                if rc_mana>y: unicorn.set_pixel(x, 7-y, ImageColor.getrgb("limegreen"))
                if vp_mana>y: unicorn.set_pixel(x+2, 7-y, ImageColor.getrgb("dodgerblue"))
            unicorn.show()
            time.sleep(global_speed*2)                
        time.sleep(global_speed*7)

        return


    def scroll_mana(): # scroll through your current vp and rc
        items = []
        process_line("colour:dodgerblue")

        vp_mana = acc.get_voting_power(with_regeneration=True)
        items.append(process_line("image:upvote.png"))
        items.append(process_line("text: manabar "))
        items.append(process_line("image:upvote.png"))
        items.append(process_line("text: VP {0:.2f} ".format(round(vp_mana,2))))

        process_line("colour:limegreen")
        rc_mana = acc.get_rc_manabar()['estimated_pct']
        items.append(process_line("text:RC {} ".format(round(rc_mana))))
        image = render(items)
        scroll(image)
        return

    def scrool_unclaimed(): # scroll through unclaimed rewards
        items = []
        unclaimed_sbd = round(float(acc.get_balance("rewards", "SBD")),2)
        unclaimed_steem = round(float(acc.get_balance("rewards", "STEEM")),2)
        unclaimed_sp = round(float(steem.vests_to_sp(acc.get_balance("rewards", "VESTS"))),2)
        process_line("colour:orange")
        
        if unclaimed_sbd + unclaimed_steem + unclaimed_sbd > 0:
            items.append(process_line("image:unclaimed.png"))
            items.append(process_line("text: unclaimed rewards "))
            items.append(process_line("image:unclaimed.png"))

            if unclaimed_sbd>0: 
                items.append(process_line("text: SBD {0:.2f}".format(unclaimed_sbd)))
            if unclaimed_steem>0: 
                items.append(process_line("image:unclaimed.png"))
                items.append(process_line("text: STEEM {0:.2f}".format(unclaimed_steem)))
            if unclaimed_sp>0: 
                items.append(process_line("image:unclaimed.png"))
                items.append(process_line("text: SP {0:.2f}".format(unclaimed_sp)))
            image = render(items)
            scroll(image)
        return

    def scroll_last_rewards(): # scroll through the estimated rewards for your last 3 posts
        items = []
        process_line("colour:DarkMagenta")
        items.append(process_line("text: *** est. payouts ***"))

        for post in acc.blog_history(reblogs=False, limit=3):
            comment = Comment("{}/{}".format(post.author,post.permlink))
            rewards = comment.get_rewards()['total_payout']
            items.append(process_line("text: {}".format(rewards)))
        image = render(items)
        scroll(image)
        return

    def scroll_last_comments(): # scroll through first 25characters of the last 3 replies
        items = []
        process_line("colour:Red")
        items.append(process_line("text: *** comments ***"))
        for reply in acc.reply_history(limit=3):
            reply_body = reply.body   
            body = (reply_body[:25] + '..') if len(reply_body) > 25 else reply_body
            items.append(process_line("text: {} * {} * ".format(reply.author, body.replace('\n',' - '))))

        image = render(items)
        scroll(image)
        return


# Set medium brightness to start
set_brightness(10)

# Main loop
while True:
    if connect_steem: 
        
        
        scroll_mana()
        scrool_unclaimed()
        mana_bars()
        scroll_last_comments()
        scroll_last_rewards()        
        mana_bars()
    else: 
        print_time()
