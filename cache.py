import hashlib
import os
import zlib
def filename(request):
    hash = hashlib.sha1(request).hexdigest()
    path = os.path.join("cache",os.path.join(hash[0:2],hash[2:]))
    return path

def load(request):
    fn = filename(request)
    if os.path.exists(fn):
        f = open(fn,"r")
        data = f.read()
        f.close()
        return zlib.decompress(data)
    return None

def store(request,data):
    fn = filename(request)
    try:
        os.makedirs(os.path.dirname(fn))
    except OSError:
        pass
    f = open(fn,"w")
    f.write(zlib.compress(data))
    f.close()
