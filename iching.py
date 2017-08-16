import numpy as np
import re
import svgwrite
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import cairocffi as cairo

# get a random char from s, ignoring ones we don't want
def get_rand_char(s):
    ignore_chars = set([' ', '\n'])
    char_set = set(s)
    available_chars = list(char_set - ignore_chars)
    return available_chars[int(np.round(np.random.random() * (len(available_chars) - 1)))]

def get_lines(s):
    return s.split("\n")

def rm_newlines(s):
    return s.replace("\n", "")

# get n random chars from s, ensuring the full set of chars in s is present. remove all newlines.
def get_rand_chars(s, n):
    s = rm_newlines(s)
    char_set = set(s)
    unique_chars = list(char_set)
    
    rand_chars = np.random.choice(unique_chars, n)
    
    not_all_chars_used = len(char_set.difference(set(rand_chars))) > 0
    
    if not_all_chars_used:
        return get_rand_chars(s, n)
    
    return "".join(rand_chars)

def get_rand_segments(s, n):
    s = rm_newlines(s)
    

def insert_newlines(s, nchars):
    s = rm_newlines(s)
    pattern = "(.{" + str(nchars) + "})"
    return re.sub(pattern, "\\1\n", s, 0, re.DOTALL)

def get_random_line_index(s):
    lines = get_lines(s)
    return int(np.round(np.random.random() * (len(lines) - 1)))

def get_words(s):
    # select random line
    lines = get_lines(s)
    line = lines[get_random_line_index(s)]
    
    # select random words from that line
    words = line.split(" ")
    n_words = int(np.round(np.random.random() * (len(words) - 1)))
    offset = int(np.round(np.random.random() * (len(words) - n_words)))
    line_portion = words[offset:(offset + n_words)]
    return " ".join(line_portion)

def partially_unjarble(jarbled, unjarbled):
    portion = get_words(unjarbled)
    n_chars = len(portion)
    
    # select random jarbled line
    lines = get_lines(jarbled)
    rand_line_index = get_random_line_index(jarbled)
    rand_line = lines[rand_line_index]
    rand_line_wout_newln = rm_newlines(rand_line)
    
    # make sure we can fit the entire unjarbled string in this line!
    if len(rand_line_wout_newln) >= n_chars:
        offset = int(np.round(np.random.random() * (len(rand_line_wout_newln) - n_chars)))
        str_before = rand_line[0:offset]
        str_after = rand_line[offset:]
        partially_unjarbled_line = str_before + portion + str_after
        lines[rand_line_index] = partially_unjarbled_line
        return "\n".join(lines)
    else:
        return partially_unjarble(jarbled, unjarbled)

def unjarble(jarbled, unjarbled, n, count=0):
    if count == n:
        return jarbled
    else:
        partially_unjarbled = partially_unjarble(jarbled, unjarbled)
        return unjarble(partially_unjarbled, unjarbled, n, count+1)
    
# ensure no whitespace at line ends and final line
def pad(s, n_cols, break_i):
    out = []
    lines = get_lines(s)
    
    for line, i in zip(lines, np.arange(len(lines))):
        rand_char = get_rand_char(s)
        line_out = line
        # ignore line breaks between hexagram lines
        if i % break_i != 0:
            if line[0] is " ":
                line_out = rand_char + line[1:]
            elif line[-1] is " ":
                line_out = line[0:-1] + rand_char
        out.append(line_out)
    
    # final line no trailing whitespace
    new_final_line = ""
    for i in np.arange(n_cols - len(lines[-1])):
        new_final_line += get_rand_char(s)
    
    out[-1] += new_final_line
    
    return "\n".join(out)

def ensure_num_rows(s, final_n_rows, n_cols):
    n_rows = len(get_lines(s))
    rm_rows = n_rows - final_n_rows
    n_excess_chars = rm_rows * (n_cols + len("\n"))
    return s[n_excess_chars:]

def is_yang_line(i, hexagram, break_i):
    hex_line = get_hexagram_line(i, break_i)
    return hexagram[hex_line]

def get_hexagram_line(i, break_i):
    return int(np.floor(i/break_i))
    
def to_hexagram(s, n_cols, vert_gap, break_i, hexagram):
    # every 7th line blank
    lines = get_lines(s)
    out = []
    for i in np.arange(len(lines)):
        if i % break_i == 0:
            # line break
            out.append(" " * n_cols)
        else:
            # divided or solid ; yin/yang?
            if is_yang_line(i, hexagram, break_i):
                out.append(lines[i])
            else:
                # insert gap in line to make yin
                offset_begin = len(lines[i])/2 - vert_gap/2
                offset_end = offset_begin + vert_gap
                yin = ""
                for ii in np.arange(len(lines[i])):
                    # clean ur vertical gap 
                    flanks_gap = (ii == offset_begin-1) or (ii == offset_end)
                    if lines[i][ii] == " " and flanks_gap:
                        yin += get_rand_char(s)
                    elif ii >= offset_begin and ii < offset_end:
                        yin += " "
                    else:
                        yin += lines[i][ii]
                
                out.append(yin)
    
    return "\n".join(out)

# final text comprises final chars
def append_txt(s, final):
    offset = len(s) - len(final)
    out = ""
    for i in np.arange(len(s)):
        ii = len(s) - i
        doit = False
        try:
            # respect existing line breaks
            doit = not (s[ii-1]+s[ii] == "\n") or (s[ii]+s[ii+1] == "\n")
        except IndexError:
            print('bad char i')
        if doit:
            if i < offset:
                out += s[i]
            else:
                final_offset = i - offset
                out += final[final_offset]
    return out

# finalize the shape into an appropriate shape
def reshape(s, n_rows, n_cols, vert_gap, line_break, hexagram):
    # format lines
    s1 = insert_newlines(s, n_cols)

    # rm excess rows
    s1 = ensure_num_rows(s1, n_rows, n_cols)

    # form lines as hexagram
    s1 = to_hexagram(s1, n_cols, vert_gap, line_break, hexagram)

    # format whitespace
    s1 = pad(s1, n_cols, line_break)
    
    return s1

# draw with PIL
def draw_pil_txt(s, size, title, font, font_color, font_size):
    
    image = Image.new("RGBA", size, (255,255,255))
    draw = ImageDraw.Draw(image)
    
    wt, ht = draw.textsize(title, font)
    wp, hp = draw.textsize(s, font)
    
    # title
    draw.text(((size[0]-wt)/2, size[1]/2 - hp/2 - font_size*2), title, font=font, fill=font_color)
    
    # poem
    draw.text(((size[0]-wp)/2, (size[1]-hp)/2), s, font=font, fill=font_color)
    
    return image

# draw with Cairo
def draw_cairo_txt(s, size, title, font, font_color, font_size):
    
    # setup a place to draw
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size[0], size[1])
    ctx = cairo.Context (surface)

    # paint background
    ctx.set_source_rgb(1, 1, 1)
    ctx.rectangle(0, 0, size[0], size[1])
    ctx.fill()

    # draw text
    ctx.select_font_face(font)
    ctx.set_font_size(font_size)
    ctx.set_source_rgb(0,0,0)
    
    lines = get_lines(s)
    
    # title
    xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(title)
    ctx.move_to(size[0]/2 - width/2, size[1]/2 - (font_size*len(lines))/2 - font_size*2)
    ctx.show_text(title)
    
    # we have to position each line individually :(
    for line, i in zip(lines, np.arange(len(lines))):
        xbearing, ybearing, width, height, xadvance, yadvance = ctx.text_extents(line)
        print(line)
        ctx.move_to(size[0]/2 - width/2, size[1]/2 - (font_size*len(lines))/2 + i * font_size)
        ctx.show_text(line)

    ctx.stroke()
    return surface