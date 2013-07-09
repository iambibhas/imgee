# -*- coding: utf-8 -*-

import os.path
import re
import mimetypes
from StringIO import StringIO
from PIL import Image

from boto import connect_s3
from boto.s3.bucket import Bucket
from boto.s3.key import Key

from imgee import app
from imgee.models import db, Thumbnail
from imgee.utils import newid, guess_extension
from imgee.models import StoredFile


def get_s3_bucket():
    conn = connect_s3(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
    bucket = Bucket(conn, app.config['AWS_BUCKET'])
    return bucket


def get_width_height(img_path):
    try:
        img = Image.open(img_path)
    except:
        return (0, 0)
    else:
        return img.size


def save_in_db(name, title, local_path, profile, mimetype):
    size_in_bytes = os.path.getsize(local_path)
    width, height = get_width_height(local_path)
    stored_file = StoredFile(name=name, title=title, profile=profile,
                    size=size_in_bytes, width=width, height=height, mimetype=mimetype)
    db.session.add(stored_file)
    db.session.commit()


def save(fp, profile, img_name=None, remote=True):
    id_ = img_name or newid()
    content_type = get_file_type(fp.filename)
    img_name = "%s%s" % (id_, guess_extension(content_type))
    local_path = path_for(img_name)
    with open(local_path, 'w') as img:
        img.write(fp.read())

    save_in_db(name=id_, title=fp.filename, local_path=local_path,
                    profile=profile, mimetype=content_type)

    if remote:
        save_on_s3(local_path, img_name, content_type=content_type)


def get_file_type(filename):
    return mimetypes.guess_type(filename)[0]


def get_s3_folder(f=''):
    f = f or app.config.get('AWS_FOLDER', '')
    if f and not f.endswith('/'):
        f = f + '/'
    return f or ''


def save_on_s3(file_path, filename='', content_type='', bucket='', folder=''):
    with open(file_path) as fp:
        b = bucket or get_s3_bucket()
        folder = get_s3_folder(folder)
        filename = filename or fp.name
        k = b.new_key(folder+filename)
        content_type = content_type or get_file_type(filename)
        headers = {
            'Cache-Control': 'max-age=31536000',  # 60*60*24*365
            'Content-Type': content_type,
        }
        k.set_contents_from_file(fp, policy='public-read', headers=headers)
    return k


def path_for(img_name):
    return os.path.join(app.config['UPLOADED_FILES_DEST'], img_name)


def parse_size(size):
    """return `size` as a tuple (w, h). None if not formattable"""
    if isinstance(size, (str, unicode)):
        return split_size(size)
    elif isinstance(size, tuple) and len(size) == 2:
        return size


def get_resized_image(img, size, is_thumbnail=False):
    img_name = img.name
    size_t = parse_size(size)
    if size_t:
        size = '%sx%s' % size_t
        scaled = Thumbnail.query.filter_by(size=size, stored_file=img).first()
        if scaled:
            img_name = scaled.name
        else:
            img_name = resize_and_save(img, size_t, is_thumbnail=is_thumbnail)
    return img_name


def get_image_locally(img_name):
    local_path = path_for(img_name)
    if not os.path.exists(local_path):
        bucket = get_s3_bucket()
        k = Key(bucket)
        k.key = img_name
        k.get_contents_to_filename(local_path)
    return local_path


def get_resized_name(img, size):
    w, h = size
    if w and h:
        name = '%s_w%s_h%s' % (img.name, w, h)
    elif w:
        name = '%s_w%s' % (img.name, w)
    elif h:
        name = '%s_h%s' % (img.name, h)
    else:
        name = img.name
    return name


def resize_and_save(img, size, is_thumbnail=False):
    extn = img.extn
    src_path = get_image_locally(img.name+extn)
    scaled_img_name = get_resized_name(img, size)
    content_type = get_file_type(img.title)  # eg: image/jpeg
    format = guess_extension(content_type).lstrip('.')
    scaled_path = resize_img(src_path, size, format, is_thumbnail=is_thumbnail)
    save_on_s3(scaled_path, scaled_img_name+extn, content_type)
    size_s = "%sx%s" % size
    scaled = Thumbnail(name=scaled_img_name, size=size_s, stored_file=img)
    db.session.add(scaled)
    db.session.commit()
    return scaled_img_name


def get_size((orig_w, orig_h), (w, h)):
    # fit the image to the box along the smaller side and preserve aspect ratio.
    # w or h being 0 means preserve aspect ratio with that height or width

    if (h == 0) or (orig_w <= orig_h):
        size = (w, w*orig_h/orig_w)
    else:
        size = (h*orig_w/orig_h, h)

    size = map(lambda x: max(x, 1), size)   # let the width or height be atleast 1px.
    return map(int, size)


def resize_img(src, size, format, is_thumbnail):
    """
    `size` is a tuple (width, height)
    resize the image at `src` to the specified `size` and return the resized img.
    """
    if (not size) or (not os.path.exists(src)):
        return
    img = Image.open(src)
    img.load()

    size = get_size(img.size, size)
    resized = img.resize(size, Image.ANTIALIAS)

    if is_thumbnail:
        # and crop the rest, keeping the center.
        w, h = resized.size
        tw, th = app.config.get('THUMBNAIL_SIZE')
        left, top = int((w-tw)/2), int((h-th)/2)
        resized = resized.crop((left, top, left+tw, top+th))

    name, extn = os.path.splitext(src)
    resized_path = '%s_%sx%s%s' % (name, size[0], size[1], extn)
    resized.save(resized_path, format=format, quality=100)
    return resized_path


def split_size(size):
    """ return (w, h) if size is 'wxh'
    """
    r = r'^(\d+)(x(\d+))?$'
    matched = re.match(r, size)
    if matched:
        w, h = matched.group(1, 2)
        h = int(h.lstrip('x')) if h is not None else 0
        return int(w), h


def delete_on_s3(stored_file):
    """
    Delete all the thumbnails and images associated with a file
    """
    extn = stored_file.extn
    keys = [(get_s3_folder() + thumbnail.name + extn) for thumbnail in stored_file.thumbnails]
    keys.append(get_s3_folder() + stored_file.name + extn)
    bucket = get_s3_bucket()
    bucket.delete_keys(keys)
