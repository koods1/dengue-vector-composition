"""Probe a remote NEX-GDDP NetCDF4/HDF5 file over HTTP range requests to see
whether spatial subsetting can reduce transfer. If the variable is chunked as
whole global fields per day, subsetting buys nothing and full files must be
downloaded."""
import urllib.request, io, sys
import h5py
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

URL = ('https://nex-gddp-cmip6.s3.amazonaws.com/NEX-GDDP-CMIP6/GFDL-ESM4/'
       'historical/r1i1p1f1/tas/tas_day_GFDL-ESM4_historical_r1i1p1f1_gr1_2000_v2.0.nc')

class HttpFile(io.RawIOBase):
    """Minimal seekable read-only file over HTTP byte ranges."""
    def __init__(self, url):
        self.url = url
        self.pos = 0
        self.nreq = 0
        self.nbytes = 0
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=120) as r:
            self.size = int(r.headers['Content-Length'])
    def readable(self): return True
    def seekable(self): return True
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos
    def tell(self): return self.pos
    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0:
            return b''
        end = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(self.url,
                                     headers={'Range': f'bytes={self.pos}-{end}'})
        with urllib.request.urlopen(req, timeout=300) as r:
            d = r.read()
        self.nreq += 1
        self.nbytes += len(d)
        self.pos += len(d)
        return d

    def readinto(self, b):
        d = self.read(len(b))
        b[:len(d)] = d
        return len(d)

f = HttpFile(URL)
print(f'file size {f.size:,} bytes')
h = h5py.File(f, 'r')
print('variables:', list(h.keys()))
v = h['tas']
print(f'  shape      {v.shape}')
print(f'  dtype      {v.dtype}')
print(f'  chunks     {v.chunks}')
print(f'  compression{"":1s} {v.compression}')
if v.chunks:
    cb = 1
    for c, s in zip(v.chunks, v.shape):
        cb *= c
    print(f'  chunk elements {cb:,} = {cb * v.dtype.itemsize / 1e6:.1f} MB uncompressed')
    ny, nx = v.shape[1], v.shape[2]
    # study window fraction
    frac = (50 / 180) * (76 / 360)
    print(f'\n  study window is {100 * frac:.1f}% of the globe')
    if v.chunks[1] >= ny and v.chunks[2] >= nx:
        print('  VERDICT: chunked as whole global fields -> spatial subsetting '
              'saves nothing; full files must be downloaded.')
    else:
        print('  VERDICT: spatially chunked -> subsetting can reduce transfer.')
print(f'\nHTTP requests so far: {f.nreq}, bytes fetched {f.nbytes:,} '
      f'({100 * f.nbytes / f.size:.2f}% of file)')
